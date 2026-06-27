from shared.icons_svg import nm_svg_pixmap

pix = nm_svg_pixmap('check', '#3c8a6b', 64)
print(f'Pixmap: {pix}')
if pix:
    print(f'Is null: {pix.isNull()}')
    print(f'Size: {pix.width()}x{pix.height()}')
    pix.save('qa/_captures_v8/check_icon_test.png')
    print('Saved')
else:
    print('No pixmap')
