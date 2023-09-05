import segno

link = 'https://linkr.bio/sss_mathematics'
qrcode = segno.make_qr(link)
qrcode.save('discord_ugy.png', scale=10, light='#000000', dark='#ffffff')