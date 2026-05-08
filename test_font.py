import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" # just a dummy path, or we can use our downloaded one if it was there
# Let's just check the API
print(hasattr(fm.fontManager, 'addfont'))
