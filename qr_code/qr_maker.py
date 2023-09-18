import segno

link = 'https://linkr.bio/sss_mathematics'
qrcode = segno.make_qr(link)
qrcode.save('ugy_links_white.png', scale=20)#, light='#ffffff', dark='#ffffff')


# stack image in a grid in a4 paper size
from PIL import Image
from PIL import ImageFont

# create a new blank image
new_im = Image.new('RGB', (2480, 3508), color = (255, 255, 255))
# new_im = Image.new('RGB', (2480, 3508), color = (0, 0, 0))

# get an image
im1 = Image.open('ugy_links_white.png')
size = 750
# paste image at location (0, 0)
for i in range(0, 5):
    for j in range(0, 3):
        new_im.paste(im1, (size*j, i*size))

# save the image
new_im.save('ugy_links_white_a4.png')