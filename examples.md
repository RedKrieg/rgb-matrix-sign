`convert elmocry.webp -depth 8 -coalesce -gravity South -chop 0x100 -scale 64x32 -fuzz 10% +dither -deconstruct -layers Optimize +map elmocry.gif`

Trims the bottom 100 pixels off first, then scales to 64x32

`convert d20full.gif -background black -depth 8 -coalesce -gravity center -extent 2:1 -resize 64x32 -alpha off -dispose 1 -deconstruct -layers Optimize +map dicetest.gif`

Trims the top and bottom to 2:1 ratio, then resizes to 64x32

`convert d20full.gif -background black -depth 8 -coalesce -gravity center -resize 64x32 -extent 64x32 -alpha off -dispose 1 -deconstruct -layers Optimize +map dicetest.gif`

Resize to 64x32 then pad the left and right of the image with black


Font repo at https://github.com/olikraus/u8g2/tree/master/tools/font/bdf
