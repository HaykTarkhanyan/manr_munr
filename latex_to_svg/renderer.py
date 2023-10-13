# 13.10.23
import os
import matplotlib.pyplot as plt
from dict_to_render import to_render

# matplotlib: force computer modern font set
plt.rc('mathtext', fontset='cm')


def tex2svg(formula, save_path, fontsize=12, dpi=300):
    """Render TeX formula to SVG.
    Args:
        formula (str): TeX formula.
        save_path(str): Path to save SVG file (with extension)
        fontsize (int, optional): Font size.
        dpi (int, optional): DPI.
    Returns:
        str: SVG render.
    """
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, r'{}'.format(formula), fontsize=fontsize)

    fig.savefig(save_path, dpi=dpi, transparent=True, format='svg',
                bbox_inches='tight', pad_inches=0.0)
    plt.close(fig)

    

def main():
    print(f"Հեսա կսարքեմ svg-ներ {len(to_render)} վիդեոյի համար")
    
    videos = list(to_render.keys())
    print(f"Վիդեներ՝ {videos}", end="\n\n")
    
    for v in videos:
        if not os.path.exists(os.path.join("out", v)):
            os.mkdir(os.path.join("out", v))
        
        print(f"------ {v} ------")
        latexes = to_render[v]
        for name, latex in latexes.items():
            print(f"Սարքում եմ {name}-ը")
            tex2svg(latex, os.path.join("out", v, f"{name}.svg"))
        print(f"Ավարտվեց <<{v}>>, սարքեցի {len(latexes)} հատ svg", end="\n\n") 
           


if __name__ == '__main__':
    main()