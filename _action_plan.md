# PLAN DE ACCIÓN - PROBLEMAS CRÍTICOS NEUROMOOD

## FASE 1: RECURSOS QT SIN LIMPIAR (Prioridad Máxima)

### Archivo: shared/components_qt.py

#### Problema: Temporizadores y animaciones Qt creados pero no limpiados
- Líneas afectadas: 155, 161, 188, 275, 517, 540, 610, 736, 747, 797, 800, 1172, 1270, 1311

#### Solución requerida:
1. Implementar métodos `cleanup()` en clases que crean recursos Qt
2. Conectar señales de destrucción de widgets para liberar recursos automáticamente
3. Usar `QPointer` para verificar validez de objetos antes de usarlos
4. Implementar patrón RAII (Resource Acquisition Is Initialization) para recursos Qt

#### Ejemplo de solución:
```python
class NMCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations = []  # Lista para seguir animaciones
        
    def _create_animation(self):
        anim = QPropertyAnimation(self, b"geometry")
        self._animations.append(anim)
        # Conectar señal de finalización para limpiar
        anim.finished.connect(lambda: self._cleanup_animation(anim))
        return anim
        
    def _cleanup_animation(self, anim):
        if anim in self._animations:
            self._animations.remove(anim)
            
    def cleanup(self):
        # Limpiar todas las animaciones activas
        for anim in self._animations[:]:
            anim.stop()
            anim.deleteLater()
        self._animations.clear()
        
    def __del__(self):
        self.cleanup()
```

## FASE 2: MANEJO DE EXCEPCIONES SILENCIOSAS (Prioridad Máxima)

### Archivo: shared/theme_qt.py

#### Problema: Bloques `except Exception: pass` que silencian errores
- Líneas afectadas: 828, 849, 862

#### Solución requerida:
1. Reemplazar `except Exception: pass` con manejo específico
2. Implementar logging para errores atrapados
3. Permitir que errores críticos se propaguen cuando sea apropiado

#### Ejemplo de solución:
```python
# ANTES:
try:
    _PREMIUM_FONT_FAMILY = _load_premium_fonts()
except Exception:
    _PREMIUM_FONT_FAMILY = None

# DESPUÉS:
try:
    _PREMIUM_FONT_FAMILY = _load_premium_fonts()
except Exception as e:
    import logging
    logging.warning(f"Fallo al cargar fuentes premium: {e}")
    _PREMIUM_FONT_FAMILY = None
```

## FASE 3: CONEXIONES DE SEÑALES SIN DESCONECTAR (Prioridad Alta)

### Archivo: shared/components_qt.py

#### Problema: Conexiones ThemeManager que persisten innecesariamente
- Líneas afectadas: 127, 288, 391, 477, 523, 615, 923, 1032, 1315, 1397

#### Solución requerida:
1. Implementar desconexión explícita de señales en destrucción
2. Crear sistema de gestión automática de conexiones
3. Usar weak references para evitar ciclos de referencia

#### Ejemplo de solución:
```python
class ThemeManager(QObject):
    def connect_widget(self, widget, callback):
        """Conectar widget con gestión automática de desconexión"""
        self.theme_changed.connect(callback)
        # Guardar referencia débil para limpieza automática
        if not hasattr(widget, '_theme_connections'):
            widget._theme_connections = []
        widget._theme_connections.append(callback)
        
    def disconnect_widget(self, widget):
        """Desconectar todas las señales de un widget"""
        if hasattr(widget, '_theme_connections'):
            for callback in widget._theme_connections:
                try:
                    self.theme_changed.disconnect(callback)
                except RuntimeError:
                    # Ya desconectado
                    pass
            widget._theme_connections.clear()

# En widgets:
def _apply_theme(self, modo):
    # Implementación existente
    
def cleanup(self):
    """Método de limpieza"""
    _tm().disconnect_widget(self)
```

## FASE 4: WIDGETS SIN SEÑAL DE DESTRUCCIÓN (Prioridad Alta)

### Archivo: shared/components_qt.py

#### Problema: Widgets sin conexión de señal de destrucción del padre
- Línea afectada: 1167

#### Solución requerida:
1. Conectar señal `destroyed` de widgets para limpieza automática
2. Implementar métodos de limpieza explícitos

#### Ejemplo de solución:
```python
def __init__(self, parent=None):
    super().__init__(parent)
    # Conectar señal de destrucción para limpieza
    if parent:
        parent.destroyed.connect(self.cleanup)
    self.destroyed.connect(self.cleanup)
    
def cleanup(self):
    """Limpieza de recursos al destruir widget"""
    # Detener temporizadores
    if hasattr(self, '_timer') and self._timer:
        self._timer.stop()
        self._timer.deleteLater()
        
    # Limpiar animaciones
    if hasattr(self, '_animations'):
        for anim in self._animations:
            anim.stop()
            anim.deleteLater()
        self._animations.clear()
```

## FASE 5: CÓDIGO DUPLICADO (Prioridad Media)

### Archivos múltiples

#### Problema: Funciones `_apply_theme` duplicadas
- Múltiples archivos tienen implementaciones similares

#### Solución requerida:
1. Crear clase base común con implementación única
2. Extraer lógica común a funciones utilitarias
3. Usar mixins o composición para compartir comportamiento

#### Ejemplo de solución:
```python
class ThemeAwareWidgetMixin:
    """Mixin para widgets que necesitan aplicar temas"""
    
    def _apply_theme_base(self, modo):
        """Implementación base compartida"""
        self._modo = norm_modo(modo)
        self.update()
        
    def _apply_theme_palette(self, modo):
        """Aplicar paleta de colores"""
        c = colors(modo)
        # Lógica común de paleta
        
class NMCard(QFrame, ThemeAwareWidgetMixin):
    def _apply_theme(self, modo):
        self._apply_theme_base(modo)
        self._apply_theme_palette(modo)
        # Lógica específica del widget
```

Este plan de acción aborda los problemas más críticos identificados en la auditoría y proporciona soluciones específicas para cada categoría de problema.