import tkinter as tk
from tkinter import messagebox
import pytesseract
import pyautogui
import pyperclip
import os
import sys
from tkinter import font as tkfont
from tkinter import ttk

# Obtener la ruta del directorio donde está el ejecutable
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Configurar la ruta de Tesseract
tesseract_path = os.path.join(application_path, 'Tesseract-OCR', 'tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_path


class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = '#2C3E50'
        self['fg'] = '#00FF00'

    def on_leave(self, e):
        self['background'] = self.defaultBackground
        self['fg'] = '#00FF00'


class RecortadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reconocimiento de Texto")
        self.root.iconbitmap("texto.ico")

        # Configurar el tema oscuro futurista
        self.root.configure(bg='#1a1a1a')


        # Crear un estilo futurista
        self.style = {
            'bg': '#1a1a1a',
            'fg': '#00FF00',
            'button_bg': '#2C3E50',
            'button_fg': '#00FF00',
            'highlight': '#3498DB'
        }

        # Agregar menú de opciones
        self.menu_bar = tk.Menu(root, bg=self.style['bg'], fg=self.style['fg'], tearoff=0)
        self.root.config(menu=self.menu_bar)

        # Menú "Acerca de..."
        self.menu_bar.add_command(
            label="Acerca de...",
            command=self.mostrar_acerca_de
        )

        # Verificar si Tesseract está disponible
        if not os.path.exists(tesseract_path):
            self.mostrar_error_tesseract()
            return

        # Canvas principal con scroll
        self.canvas_main = tk.Canvas(root, bg=self.style['bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas_main.yview)
        self.scrollable_frame = tk.Frame(self.canvas_main, bg=self.style['bg'])

        # Configurar el scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_main.configure(
                scrollregion=self.canvas_main.bbox("all")
            )
        )

        # Crear ventana en el canvas para el frame scrollable
        self.canvas_main.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=580)
        self.canvas_main.configure(yscrollcommand=self.scrollbar.set)

        # Empaquetar el canvas y la scrollbar
        self.canvas_main.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        self.scrollbar.pack(side="right", fill="y", pady=20)

        # Configurar el evento del mouse para el scroll
        self.canvas_main.bind_all("<MouseWheel>", self._on_mousewheel)

        # Título con efecto futurista
        title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.title_frame = tk.Frame(self.scrollable_frame, bg=self.style['bg'])
        self.title_frame.pack(fill='x', pady=(0, 20))

        self.title_label = tk.Label(self.title_frame,
                                    text="SISTEMA DE RECONOCIMIENTO DE TEXTO",
                                    font=title_font,
                                    bg=self.style['bg'],
                                    fg=self.style['fg'])
        self.title_label.pack()

        # Separador decorativo
        self.separator = tk.Canvas(self.scrollable_frame, height=2, bg=self.style['bg'], highlightthickness=0)
        self.separator.pack(fill='x', pady=(0, 20))
        self.separator.create_line(0, 1, 800, 1, fill=self.style['highlight'])

        # Frame para el área de texto
        self.text_frame = tk.Frame(self.scrollable_frame, bg=self.style['bg'])
        self.text_frame.pack(fill='both', expand=True)

        # Área de texto con borde brillante
        self.texto_label = tk.Label(self.text_frame,
                                    text="|::|TEXTO RECONOCIDO|::|\n*************☺***************",
                                    font=('Courier', 12),
                                    bg='#2a2a2a',
                                    fg=self.style['fg'],
                                    relief='solid',
                                    bd=1,
                                    padx=10,
                                    pady=10,
                                    wraplength=500)  # Añadir wraplength para que el texto se ajuste
        self.texto_label.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame para botones
        self.button_frame = tk.Frame(self.scrollable_frame, bg=self.style['bg'])
        self.button_frame.pack(pady=20)

        # Botones con efecto hover
        self.boton_nuevo = HoverButton(self.button_frame,
                                       text="NUEVO ESCANEO",
                                       command=self.abrir_ventana_previa,
                                       bg=self.style['button_bg'],
                                       fg=self.style['button_fg'],
                                       font=('Helvetica', 10, 'bold'),
                                       width=15,
                                       relief='flat')
        self.boton_nuevo.pack(side='left', padx=5)

        self.boton_copiar = HoverButton(self.button_frame,
                                        text="COPIAR TEXTO",
                                        command=self.copiar_texto,
                                        bg=self.style['button_bg'],
                                        fg=self.style['button_fg'],
                                        font=('Helvetica', 10, 'bold'),
                                        width=15,
                                        relief='flat')
        self.boton_copiar.pack(side='left', padx=5)

        # Configuración de la ventana de vista previa
        self.texto_reconocido_lista = []
        self.start_x = None
        self.start_y = None
        self.imagen_recortada = None

        self.ventana_previa = tk.Toplevel(root)
        self.ventana_previa.title("Vista Previa")
        self.ventana_previa.attributes("-fullscreen", True)
        self.ventana_previa.attributes("-alpha", 0.3)  # Más transparente para efecto futurista
        self.ventana_previa.protocol("WM_DELETE_WINDOW", self.cerrar_ventana_previa)
        self.ventana_previa.withdraw()

        # Canvas con borde de neón
        self.canvas_previa = tk.Canvas(self.ventana_previa,
                                       bg='black',
                                       highlightthickness=2,
                                       highlightbackground="#00FF00")
        self.canvas_previa.pack(expand=True, fill='both')

        # Eventos del canvas
        self.canvas_previa.bind("<ButtonPress-1>", self.iniciar_seleccion)
        self.canvas_previa.bind("<B1-Motion>", self.actualizar_seleccion)
        self.canvas_previa.bind("<ButtonRelease-1>", self.recortar_imagen)

        # Ventana principal más alta para mostrar más contenido
        window_width = 600
        window_height = 500
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def mostrar_acerca_de(self):
        """Mostrar información del desarrollador."""
        acerca_de_ventana = tk.Toplevel(self.root)
        acerca_de_ventana.title("Acerca de...")
        acerca_de_ventana.configure(bg=self.style['bg'])

        # Obtener el tamaño de la pantalla y la ventana
        window_width = 300
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calcular la posición para centrar la ventana
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2

        # Configurar la geometría de la ventana centrada
        acerca_de_ventana.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Etiqueta con el texto de autor
        etiqueta_autor = tk.Label(
            acerca_de_ventana,
            text="Hecho Por: Juan Gabriel Febre Carrion",
            bg=self.style['bg'],
            fg=self.style['fg'],
            font=("Helvetica", 12, "bold"),
            wraplength=280
        )
        etiqueta_autor.pack(expand=True, padx=10, pady=10)

        # Botón para cerrar
        boton_cerrar = HoverButton(
            acerca_de_ventana,
            text="Cerrar",
            command=acerca_de_ventana.destroy,
            bg=self.style['button_bg'],
            fg=self.style['button_fg'],
            font=("Helvetica", 10, "bold"),
            relief="flat"
        )
        boton_cerrar.pack(pady=10)

    def _on_mousewheel(self, event):
        """Maneja el evento de la rueda del mouse para el scroll"""
        self.canvas_main.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def mostrar_error_tesseract(self):
        error_label = tk.Label(self.root,
                               text="ERROR: NO SE DETECTÓ TESSERACT-OCR\n" +
                                    "Verifique que la carpeta 'Tesseract-OCR'\n" +
                                    "esté en el directorio del programa",
                               fg='#FF0000',
                               bg=self.style['bg'],
                               font=('Helvetica', 12, 'bold'))
        error_label.pack(pady=20)

    def actualizar_seleccion(self, event):
        try:
            cur_x = event.x
            cur_y = event.y
            self.canvas_previa.delete("rect_previa")
            self.canvas_previa.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline="#00FF00",  # Color neón
                width=2,  # Línea más gruesa
                tags="rect_previa"
            )
            self.ventana_previa.update_idletasks()
        except Exception as e:
            print(f"Error al actualizar selección: {e}")


    def actualizar_etiqueta_texto(self):
        texto_actualizado = "\n".join(self.texto_reconocido_lista)
        self.texto_label.config(
            text=f"╔══ TEXTO RECONOCIDO ══╗\n\n{texto_actualizado}\n\n╚════════════════════╝"
        )
        # Asegurar que el scroll se actualice después de cambiar el texto
        self.scrollable_frame.update_idletasks()
        self.canvas_main.configure(scrollregion=self.canvas_main.bbox("all"))

    # Los demás métodos permanecen igual...
    def abrir_ventana_previa(self):
        self.root.withdraw()
        self.ventana_previa.deiconify()

    def cerrar_ventana_previa(self):
        self.ventana_previa.withdraw()
        self.root.deiconify()

    def iniciar_seleccion(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def recortar_imagen(self, event):
        self.ventana_previa.withdraw()
        self.texto_reconocido_lista.clear()

        try:
            if self.start_x is not None and self.start_y is not None:
                cur_x = event.x
                cur_y = event.y
                area_seleccionada = (
                    int(min(self.start_x, cur_x)),
                    int(min(self.start_y, cur_y)),
                    int(max(self.start_x, cur_x)),
                    int(max(self.start_y, cur_y))
                )
                screenshot = pyautogui.screenshot()
                self.imagen_recortada = screenshot.crop(area_seleccionada)
                self.imagen_recortada.save('recorte_temporal.png', format='PNG')
                texto_reconocido = pytesseract.image_to_string('recorte_temporal.png', lang='spa')
                self.texto_reconocido_lista.append(texto_reconocido)
                self.actualizar_etiqueta_texto()
                self.start_x = None
                self.start_y = None
                self.root.deiconify()
        except Exception as e:
            print(f"Error al recortar imagen: {e}")
            self.start_x = None
            self.start_y = None
            self.root.deiconify()

    def copiar_texto(self):
        texto_completo = "\n".join(self.texto_reconocido_lista)
        pyperclip.copy(texto_completo)


if __name__ == "__main__":
    root = tk.Tk()
    app = RecortadorApp(root)
    root.mainloop()