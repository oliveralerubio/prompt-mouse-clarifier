"""Small Tkinter configuration UI for providers and mouse bindings."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config import config_path, load, save
from .prompt import PROMPT_SYSTEM

ACTIONS = ["none", "clarify", "previous_window"]
PROVIDER_KINDS = ["ollama", "openai"]


def run() -> None:
    data = load()
    root = tk.Tk()
    root.title("Prompt Mouse Clarifier")
    root.geometry("860x700")
    root.minsize(760, 600)

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)
    main.columnconfigure(0, weight=1)
    main.columnconfigure(1, weight=1)
    main.rowconfigure(2, weight=1)
    main.rowconfigure(5, weight=1)

    ttk.Label(main, text="Prompt Mouse Clarifier", font=("TkDefaultFont", 16, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w"
    )
    ttk.Label(
        main,
        text="Configura qué hace cada botón y qué modelo transforma tus prompts.",
    ).grid(row=1, column=0, columnspan=2, pady=(4, 14), sticky="w")

    settings = data.setdefault("settings", {})
    provider_data = data.setdefault("providers", [])

    # Provider panel
    provider_frame = ttk.LabelFrame(main, text="Proveedor del Prompt Enhancer", padding=10)
    provider_frame.grid(row=2, column=0, padx=(0, 8), sticky="nsew")
    provider_frame.columnconfigure(0, weight=1)
    provider_frame.rowconfigure(0, weight=1)

    provider_list = tk.Listbox(provider_frame, height=8, exportselection=False)
    provider_list.grid(row=0, column=0, columnspan=2, sticky="nsew")
    provider_scroll = ttk.Scrollbar(provider_frame, orient="vertical", command=provider_list.yview)
    provider_scroll.grid(row=0, column=2, sticky="ns")
    provider_list.configure(yscrollcommand=provider_scroll.set)

    form = ttk.Frame(provider_frame)
    form.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
    form.columnconfigure(1, weight=1)
    provider_vars = {
        key: tk.StringVar()
        for key in ("name", "kind", "base_url", "model", "api_key_env", "timeout")
    }
    labels = [
        ("name", "Nombre"),
        ("kind", "Tipo"),
        ("base_url", "URL base"),
        ("model", "Modelo"),
        ("api_key_env", "Variable API key"),
        ("timeout", "Timeout (s)"),
    ]
    for row, (key, label) in enumerate(labels):
        ttk.Label(form, text=label).grid(row=row, column=0, padx=(0, 8), pady=3, sticky="w")
        if key == "kind":
            widget = ttk.Combobox(form, textvariable=provider_vars[key], values=PROVIDER_KINDS, state="readonly")
        else:
            widget = ttk.Entry(form, textvariable=provider_vars[key])
        widget.grid(row=row, column=1, pady=3, sticky="ew")

    provider_index: dict[str, int | None] = {"value": None}

    def refresh_providers(select: int | None = None) -> None:
        provider_list.delete(0, "end")
        for item in provider_data:
            provider_list.insert(
                "end",
                f"{item.get('name', '')} · {item.get('kind', '')} · {item.get('model', '')}",
            )
        if select is not None and 0 <= select < len(provider_data):
            provider_list.selection_set(select)
            provider_list.activate(select)
            provider_list.see(select)
            load_provider(select)

    def load_provider(index: int) -> None:
        item = provider_data[index]
        provider_index["value"] = index
        for key in provider_vars:
            provider_vars[key].set(str(item.get(key, "")))
        if not provider_vars["timeout"].get():
            provider_vars["timeout"].set("45")

    def on_provider_select(_event=None) -> None:
        selected = provider_list.curselection()
        if selected:
            load_provider(selected[0])

    def provider_from_form() -> dict:
        name = provider_vars["name"].get().strip()
        kind = provider_vars["kind"].get().strip()
        base_url = provider_vars["base_url"].get().strip().rstrip("/")
        model = provider_vars["model"].get().strip()
        if not all((name, kind, base_url, model)):
            raise ValueError("Nombre, tipo, URL base y modelo son obligatorios")
        try:
            timeout = float(provider_vars["timeout"].get() or "45")
        except ValueError as exc:
            raise ValueError("El timeout debe ser un número") from exc
        if timeout <= 0:
            raise ValueError("El timeout debe ser mayor que cero")
        return {
            "name": name,
            "kind": kind,
            "base_url": base_url,
            "model": model,
            "api_key_env": provider_vars["api_key_env"].get().strip(),
            "timeout": timeout,
        }

    def add_or_update_provider() -> None:
        try:
            item = provider_from_form()
        except ValueError as exc:
            messagebox.showerror("Proveedor inválido", str(exc), parent=root)
            return
        index = provider_index["value"]
        existing = next((i for i, p in enumerate(provider_data) if p.get("name") == item["name"]), None)
        if index is None:
            if existing is not None:
                messagebox.showerror("Nombre duplicado", "Ya existe un proveedor con ese nombre.", parent=root)
                return
            provider_data.append(item)
            index = len(provider_data) - 1
        else:
            if existing is not None and existing != index:
                messagebox.showerror("Nombre duplicado", "Ya existe un proveedor con ese nombre.", parent=root)
                return
            provider_data[index] = item
        refresh_providers(index)

    def new_provider() -> None:
        provider_index["value"] = None
        for key in provider_vars:
            provider_vars[key].set("")
        provider_vars["kind"].set("openai")
        provider_vars["timeout"].set("45")

    def remove_provider() -> None:
        index = provider_index["value"]
        if index is None or not 0 <= index < len(provider_data):
            return
        removed = provider_data.pop(index)
        if settings.get("active_provider") == removed.get("name"):
            settings["active_provider"] = provider_data[0]["name"] if provider_data else ""
        new_provider()
        refresh_providers()

    provider_list.bind("<<ListboxSelect>>", on_provider_select)
    buttons = ttk.Frame(provider_frame)
    buttons.grid(row=2, column=0, columnspan=3, pady=(8, 0), sticky="ew")
    ttk.Button(buttons, text="Nuevo", command=new_provider).pack(side="left")
    ttk.Button(buttons, text="Añadir / actualizar", command=add_or_update_provider).pack(side="left", padx=6)
    ttk.Button(buttons, text="Eliminar", command=remove_provider).pack(side="left")

    # Binding panel
    binding_frame = ttk.LabelFrame(main, text="Botones del mouse", padding=10)
    binding_frame.grid(row=2, column=1, padx=(8, 0), sticky="nsew")
    binding_frame.columnconfigure(1, weight=1)
    binding_frame.columnconfigure(2, weight=1)
    ttk.Label(binding_frame, text="Botón").grid(row=0, column=0, padx=4, sticky="w")
    ttk.Label(binding_frame, text="Click").grid(row=0, column=1, padx=4, sticky="w")
    ttk.Label(binding_frame, text="Mantener").grid(row=0, column=2, padx=4, sticky="w")

    binding_vars: list[tuple[tk.StringVar, tk.StringVar, tk.StringVar, tk.StringVar]] = []
    binding_rows = ttk.Frame(binding_frame)
    binding_rows.grid(row=1, column=0, columnspan=3, sticky="nsew")
    binding_frame.rowconfigure(1, weight=1)

    def add_binding(initial: dict | None = None) -> None:
        initial = initial or {"button": "BTN_SIDE", "click": "none", "hold": "clarify"}
        row = len(binding_vars)
        button = tk.StringVar(value=initial.get("button", ""))
        click = tk.StringVar(value=initial.get("click", "none"))
        hold = tk.StringVar(value=initial.get("hold", "clarify"))
        seconds = tk.StringVar(value=str(initial.get("hold_seconds", 0.35)))
        binding_vars.append((button, click, hold, seconds))
        ttk.Entry(binding_rows, textvariable=button, width=16).grid(row=row, column=0, padx=4, pady=4, sticky="ew")
        ttk.Combobox(binding_rows, textvariable=click, values=ACTIONS, state="readonly", width=15).grid(row=row, column=1, padx=4, pady=4, sticky="ew")
        ttk.Combobox(binding_rows, textvariable=hold, values=ACTIONS, state="readonly", width=15).grid(row=row, column=2, padx=4, pady=4, sticky="ew")
        ttk.Entry(binding_rows, textvariable=seconds, width=6).grid(row=row, column=3, padx=4, pady=4)

    for item in settings.get("bindings", []):
        add_binding(item)
    if not binding_vars:
        add_binding()

    ttk.Label(binding_frame, text="Umbral hold (s)").grid(row=0, column=3, padx=4, sticky="w")
    ttk.Button(binding_frame, text="+ Añadir botón", command=add_binding).grid(row=2, column=0, columnspan=3, pady=8, sticky="w")

    # Bottom controls
    bottom = ttk.Frame(main)
    bottom.grid(row=3, column=0, columnspan=2, pady=(14, 0), sticky="ew")
    bottom.columnconfigure(1, weight=1)
    active = tk.StringVar(value=settings.get("active_provider", provider_data[0]["name"] if provider_data else ""))
    ttk.Label(bottom, text="Proveedor activo:").grid(row=0, column=0, sticky="w")
    active_combo = ttk.Combobox(bottom, textvariable=active, state="readonly", width=28)
    active_combo.grid(row=0, column=1, padx=8, sticky="w")

    def refresh_active_values() -> None:
        active_combo.configure(values=[item.get("name", "") for item in provider_data])

    def save_config() -> None:
        if active.get() and active.get() not in [p.get("name") for p in provider_data]:
            messagebox.showerror("Proveedor inválido", "El proveedor activo ya no existe.", parent=root)
            return
        settings["active_provider"] = active.get()
        settings["bindings"] = [
            {
                "button": b.get().strip(),
                "click": c.get(),
                "hold": h.get(),
                "hold_seconds": float(s.get() or "0.35"),
            }
            for b, c, h, s in binding_vars
            if b.get().strip()
        ]
        save(data)
        messagebox.showinfo("Guardado", f"Configuración guardada en:\n{config_path()}", parent=root)

    def show_prompt() -> None:
        dialog = tk.Toplevel(root)
        dialog.title("Prompt del clarificador")
        dialog.geometry("760x500")
        text = tk.Text(dialog, wrap="word")
        text.insert("1.0", PROMPT_SYSTEM)
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, padx=12, pady=12)

    ttk.Button(bottom, text="Ver prompt", command=show_prompt).grid(row=0, column=2, padx=8)
    ttk.Button(bottom, text="Guardar configuración", command=save_config).grid(row=0, column=3, padx=8)
    ttk.Label(
        main,
        text="Las API keys nunca se guardan aquí: configura la variable indicada, por ejemplo OPENROUTER_API_KEY.",
        foreground="#555",
    ).grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky="w")

    refresh_providers()
    refresh_active_values()
    root.mainloop()
