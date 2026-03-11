import os
import tempfile
import subprocess
import logging
from Xlib import X

from src.actions import apply_style_snippet

logger = logging.getLogger(__name__)

def get_latex_template(latex_content: str) -> str:
    """Wraps the raw math equation in a full LaTeX document template."""
    return r"""
        \documentclass[12pt,border=12pt]{standalone}
        \usepackage[utf8]{inputenc}
        \usepackage[T1]{fontenc}
        \usepackage{textcomp}
        \usepackage{amsmath, amssymb}
        \newcommand{\R}{\mathbb R}
        \begin{document}
    """ + latex_content + r"\end{document}"

def open_neovim(file_path: str) -> None:
    """
    Opens Neovim inside a terminal emulator. 
    This process BLOCKS Python until the user closes Neovim.
    """
    try:
        # Example: ['alacritty', '-e', 'nvim', file_path]
        subprocess.run(['alacritty', '-e', 'nvim', file_path], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Terminal emulator failed: {e}")
    except FileNotFoundError:
        logger.error("Terminal emulator not found. Check your command.")

def spawn_latex_editor(listener, compile_latex: bool = True) -> None:
    """The main pipeline for the editor popup."""
    
    # 1. Create temporary file and prefill with $$
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.tex') as f:
        f.write('$$')
        tmp_name = f.name

    try:
        # 2. Block and wait for user to type in Neovim and exit
        open_neovim(tmp_name)

        # 3. Read the typed content back
        with open(tmp_name, 'r') as f:
            content = f.read().strip()

        # Abort gracefully if the user closed Neovim without typing
        if content == '$$':
            listener.native_press('Escape', 0)
            return

        # 4. Compile the LaTeX
        if compile_latex:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.tex') as m:
                m.write(get_latex_template(content))
                m_name = m.name

            base_name = m_name[:-4]
            pdf_name = f"{base_name}.pdf"
            svg_name = f"{base_name}.svg"
            working_dir = tempfile.gettempdir()
            
            try:
                # Flag updates: Prevent freezing and capture the output to expose LaTeX errors
                subprocess.run(
                    ['pdflatex', '-halt-on-error', '-interaction=nonstopmode', m_name], 
                    cwd=working_dir, capture_output=True, text=True, check=True
                )
                subprocess.run(
                    ['pdf2svg', pdf_name, svg_name], 
                    cwd=working_dir, capture_output=True, text=True, check=True
                )
                
                with open(svg_name, 'r') as svg_file:
                    svg_content = svg_file.read()
                    
            except subprocess.CalledProcessError as e:
                # If LaTeX fails, this will print exactly why (e.g., missing package, bad syntax)
                logger.error(f"Compilation Pipeline Failed!\nCommand: {e.cmd}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
                return 
            finally:
                # This block ALWAYS executes, guaranteeing your /tmp directory stays clean
                for file_ext in ['.tex', '.pdf', '.svg', '.aux', '.log']:
                    cleanup_file = f"{base_name}{file_ext}"
                    if os.path.exists(cleanup_file):
                        os.remove(cleanup_file)
        else:
            svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg><text style="font-size:12px; font-family:'monospace'; fill:#000000; fill-opacity:1; stroke:none;" xml:space="preserve"><tspan sodipodi:role="line">{content}</tspan></text></svg>"""

        # 5. Inject into Inkscape
        apply_style_snippet(svg_content)
        listener.native_press('v', X.ControlMask)
        listener.native_press('Escape', 0)
        
    finally:
        # Guarantee the initial Neovim target file is deleted regardless of crashes
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
