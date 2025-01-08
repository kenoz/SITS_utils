import geogif

gif_img = geogif.dgif(composites, fps=8).compute()
gif_img

# as file
gif_bytes = geogif.dgif(composites, fps=8, bytes=True, robust=True).compute()

with open("example.gif", "wb") as f:
    f.write(gif_bytes)