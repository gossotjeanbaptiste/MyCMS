#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚗 Rout'Art CMS - Application de Gestion du Site
Application desktop pour gérer le contenu du site Rout'Art
Permet: Pull Git, édition HTML, préview local et Push Git
"""

from git_manager import GitManager
from html_manager import HTMLManager
from server_manager import ServerManager
from config_manager import ConfigManager
from logger import Logger
from sitemap_generator import SitemapGenerator
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
from tkinter import ttk
import customtkinter as ctk
import threading
import json
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Ajouter le chemin correct pour les imports (important pour PyInstaller)
# DOIT être fait AVANT les imports locaux
if getattr(sys, 'frozen', False):
    # Exécutable PyInstaller - les modules Python sont dans le répertoire racine
    base_dir = Path(sys._MEIPASS)
else:
    # Mode développement
    base_dir = Path(__file__).parent

sys.path.insert(0, str(base_dir))

# Imports locaux - APRÈS sys.path.insert()

# Configuration du thème CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MyCMS:
    """Application principale du CMS Rout'Art"""

    def __init__(self, root):
        self.root = root
        self.root.title("🖍️ MyCMS - Gestionnaire de Contenu (CMS)")
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)

        # Gestionnaires - INITIALISER AVANT _build_ui()
        self.config_manager = ConfigManager()
        self.logger = Logger()
        self.git_manager = GitManager(self.logger)
        self.html_manager = HTMLManager(self.logger)
        self.server_manager = ServerManager(self.logger)
        self.sitemap_generator = SitemapGenerator(self.logger)

        # Charger la configuration sauvegardée AVANT _build_ui()
        self.config_manager.load_config()

        # État de l'application
        self.repo_path = tk.StringVar(
            value=self.config_manager.get_repo_path())
        self.current_file = None
        self.current_file_content = None
        self.server_thread = None
        self.server_running = False

        # Construire l'interface
        self._build_ui()

        # Vérifier si le repo existe au démarrage
        self._on_startup()

    def _build_ui(self):
        """Construire l'interface utilisateur"""

        # Frame principal avec tabs
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Créer les tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Onglets
        self._create_git_tab()
        self._create_editor_tab()
        self._create_preview_tab()
        self._create_settings_tab()
        self._create_logs_tab()

    def _create_git_tab(self):
        """Onglet pour les opérations Git"""
        git_frame = ttk.Frame(self.notebook)
        self.notebook.add(git_frame, text="🔗 Git & Synchronisation")

        # Section Repository
        repo_section = ctk.CTkFrame(git_frame)
        repo_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(repo_section, text="Chemin du Repository:",
                     font=("Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        repo_frame = ctk.CTkFrame(repo_section)
        repo_frame.pack(fill=tk.X, pady=5)

        ctk.CTkEntry(repo_frame, textvariable=self.repo_path, height=35).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ctk.CTkButton(repo_frame, text="📁 Parcourir",
                      command=self._browse_repo, width=120, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(repo_frame, text="✓ Vérifier",
                      command=self._verify_repo, width=120, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)

        # Section Actions Git
        actions_section = ctk.CTkFrame(git_frame)
        actions_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(actions_section, text="Actions Git:", font=(
            "Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        buttons_frame = ctk.CTkFrame(actions_section)
        buttons_frame.pack(fill=tk.X, pady=10)

        ctk.CTkButton(buttons_frame, text="⬇️  Pull (Récupérer les modifications)",
                      command=self._git_pull, width=200, height=40, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(buttons_frame, text="⬆️  Push (Envoyer les modifications)",
                      command=self._git_push, width=200, height=40, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(buttons_frame, text="📊 Statut",
                      command=self._git_status, width=200, height=40, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(buttons_frame, text="➕ Ajouter des fichiers non suivis",
                      command=self._git_add_untracked, width=200, height=40, font=("Montserrat", 11)).pack(side=tk.LEFT, padx=5)

        # Message de commit
        ctk.CTkLabel(actions_section, text="Message de commit:",
                     font=("Montserrat", 11)).pack(anchor="w", pady=(15, 5))
        self.commit_message = ctk.CTkEntry(
            actions_section, placeholder_text="Exemple: Mise à jour des tarifs", height=35)
        self.commit_message.pack(fill=tk.X, pady=5)
        self.commit_message.insert(0, "Mise à jour du contenu")

        # Status panel
        status_section = ctk.CTkFrame(git_frame)
        status_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        ctk.CTkLabel(status_section, text="Statut du Repository:",
                     font=("Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        self.git_status_display = ctk.CTkTextbox(
            status_section, height=200, state="disabled", font=("Montserrat", 12))
        self.git_status_display.pack(fill=tk.BOTH, expand=True, pady=5)

    def _create_editor_tab(self):
        """Onglet pour l'édition du contenu"""
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="✏️  Éditeur de Contenu")

        # Sélection du fichier
        file_section = ctk.CTkFrame(editor_frame)
        file_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(file_section, text="Fichier à éditer:", font=(
            "Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        file_frame = ctk.CTkFrame(file_section)
        file_frame.pack(fill=tk.X, pady=5)

        self.file_combo = ctk.CTkComboBox(file_frame,
                                          values=self._get_page_files(),
                                          command=self._on_file_selected,
                                          height=35)
        self.file_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ctk.CTkButton(file_frame, text="🔄 Actualiser",
                      command=self._refresh_files, width=120).pack(side=tk.LEFT, padx=5)

        # Contenu éditable - Zone scrollable pour les éléments éditables
        content_section = ctk.CTkFrame(editor_frame)
        content_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        ctk.CTkLabel(content_section, text="Éléments Éditables (class='editable'):", font=(
            "Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        # Container avec scroll horizontal et vertical
        scroll_container = ctk.CTkFrame(content_section)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        # Cadre scrollable pour afficher les éléments éditables
        self.editable_canvas = tk.Canvas(
            scroll_container, bg="#2b2b2b", highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(
            scroll_container, orient="vertical", command=self.editable_canvas.yview)
        h_scrollbar = ttk.Scrollbar(
            scroll_container, orient="horizontal", command=self.editable_canvas.xview)

        self.editable_scrollframe = ctk.CTkFrame(
            self.editable_canvas, fg_color="#2b2b2b")

        self.editable_scrollframe.bind(
            "<Configure>",
            lambda e: self.editable_canvas.configure(
                scrollregion=self.editable_canvas.bbox("all"))
        )

        self.editable_canvas.create_window(
            (0, 0), window=self.editable_scrollframe, anchor="nw")
        self.editable_canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Bind mouse wheel scrolling
        self.editable_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.editable_canvas.bind("<Button-4>", self._on_mousewheel)
        self.editable_canvas.bind("<Button-5>", self._on_mousewheel)

        # Bind pour les éléments enfants aussi
        self.editable_scrollframe.bind("<MouseWheel>", self._on_mousewheel)
        self.editable_scrollframe.bind("<Button-4>", self._on_mousewheel)
        self.editable_scrollframe.bind("<Button-5>", self._on_mousewheel)

        self.editable_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)

        # Dictionnaire pour stocker les widgets des éléments éditables
        self.editable_fields = {}

        # Boutons d'action
        button_frame = ctk.CTkFrame(editor_frame)
        button_frame.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkButton(button_frame, text="💾 Sauvegarder", command=self._save_editable_file,
                      width=150, height=35).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="↻ Recharger", command=self._reload_file,
                      width=150, height=35).pack(side=tk.LEFT, padx=5)

    def _create_preview_tab(self):
        """Onglet pour la prévisualisation locale"""
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="👁️  Prévisualisation")

        # Section serveur
        server_section = ctk.CTkFrame(preview_frame)
        server_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(server_section, text="Serveur Local HTTP:",
                     font=("Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        server_frame = ctk.CTkFrame(server_section)
        server_frame.pack(fill=tk.X, pady=10)

        self.server_status_label = ctk.CTkLabel(
            server_frame, text="⚫ Arrêté", font=("Montserrat", 11), text_color="red")
        self.server_status_label.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(server_frame, text="Port:", font=(
            "Montserrat", 11)).pack(side=tk.LEFT, padx=5)
        self.port_entry = ctk.CTkEntry(server_frame, width=100, height=35)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        # Charger le port depuis la config
        port = self.config_manager.get_default_port()
        if isinstance(port, int) and 1 <= port <= 65535:
            self.port_entry.insert(0, str(port))
        else:
            self.port_entry.insert(0, "8000")
        # Ajouter un callback pour mettre à jour l'URL
        self.port_entry.bind("<KeyRelease>", self._update_preview_url)

        self.server_toggle_btn = ctk.CTkButton(server_frame, text="▶️  Démarrer Serveur",
                                               command=self._toggle_server, width=150, height=35)
        self.server_toggle_btn.pack(side=tk.LEFT, padx=5)

        # URL d'accès
        url_section = ctk.CTkFrame(preview_frame)
        url_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(url_section, text="URL de prévisualisation:",
                     font=("Montserrat", 11)).pack(anchor="w", pady=5)

        url_frame = ctk.CTkFrame(url_section)
        url_frame.pack(fill=tk.X, pady=5)

        self.url_label = ctk.CTkLabel(url_frame, text="http://localhost:8000",
                                      text_color="cyan", font=("Montserrat", 11, "underline"))
        self.url_label.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(url_frame, text="🌐 Ouvrir dans le navigateur",
                      command=self._open_preview, width=180).pack(side=tk.LEFT, padx=5)

        # Instructions
        info_section = ctk.CTkFrame(preview_frame)
        info_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        ctk.CTkLabel(info_section, text="Instructions:", font=(
            "Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        instructions = """
    1\t Cliquez sur "Démarrer Serveur" pour lancer un serveur local
    2\t Le serveur servira les fichiers depuis votre repository
    3\t Cliquez sur "Ouvrir dans le navigateur" pour voir le site en direct
    4\t Les modifications sauvegardées s'affichent immédiatement
    5\t Cliquez sur "Arrêter Serveur" pour terminer la session
        """

        info_label = ctk.CTkLabel(
            info_section, text=instructions, justify="left", font=("Montserrat", 13))
        info_label.pack(anchor="nw", pady=10)

        # Logs du serveur
        logs_section = ctk.CTkFrame(preview_frame)
        logs_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        ctk.CTkLabel(logs_section, text="Logs du serveur:",
                     font=("Montserrat", 11)).pack(anchor="w", pady=5)

        self.server_logs = ctk.CTkTextbox(
            logs_section, height=100, state="disabled")
        self.server_logs.pack(fill=tk.BOTH, expand=True)

    def _create_settings_tab(self):
        """Onglet pour les paramètres"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️  Paramètres")

        # Section configuration
        config_section = ctk.CTkFrame(settings_frame)
        config_section.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkLabel(config_section, text="Configuration Générale:",
                     font=("Montserrat", 12, "bold")).pack(anchor="w", pady=5)

        # Repo par défaut
        ctk.CTkLabel(config_section, text="Chemin du repository par défaut:", font=(
            "Montserrat", 11)).pack(anchor="w", pady=(10, 5))
        self.default_repo = ctk.CTkEntry(config_section, height=35)
        self.default_repo.pack(fill=tk.X, pady=5)
        self.default_repo.insert(0, self.config_manager.get_repo_path())

        # Options
        self.auto_pull_var = tk.BooleanVar(
            value=self.config_manager.get_auto_pull())
        ctk.CTkCheckBox(config_section, text="Pull automatique au démarrage",
                        variable=self.auto_pull_var).pack(anchor="w", pady=5)

        self.auto_refresh_var = tk.BooleanVar(
            value=self.config_manager.get_auto_refresh())
        ctk.CTkCheckBox(config_section, text="Rafraîchir automatiquement l'éditeur",
                        variable=self.auto_refresh_var).pack(anchor="w", pady=5)

        # Boutons
        button_frame = ctk.CTkFrame(config_section)
        button_frame.pack(fill=tk.X, pady=20)

        ctk.CTkButton(button_frame, text="💾 Sauvegarder les paramètres",
                      command=self._save_settings, width=200, height=35).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="🔄 Réinitialiser",
                      command=self._reset_settings, width=150, height=35).pack(side=tk.LEFT, padx=5)

    def _create_logs_tab(self):
        """Onglet pour les logs"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")

        # Contrôles
        controls_frame = ctk.CTkFrame(logs_frame)
        controls_frame.pack(fill=tk.X, padx=15, pady=15)

        ctk.CTkButton(controls_frame, text="🗑️  Effacer les logs",
                      command=self._clear_logs, width=150).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(controls_frame, text="💾 Exporter les logs",
                      command=self._export_logs, width=150).pack(side=tk.LEFT, padx=5)

        # Logs display
        self.logs_display = ctk.CTkTextbox(
            logs_frame, state="disabled", font=("Montserrat", 13))
        self.logs_display.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Refresh logs periodically
        self._refresh_logs_display()

    # ======= Méthodes Git =======

    def _browse_repo(self):
        """Parcourir et sélectionner un dossier"""
        path = filedialog.askdirectory(
            title="Sélectionner le dossier du repository")
        if path:
            self.repo_path.set(path)
            self.config_manager.set_repo_path(path)

    def _verify_repo(self):
        """Vérifier que le repo existe et est valide"""
        path = self.repo_path.get()
        result = self.git_manager.verify_repo(path)
        if result["valid"]:
            messagebox.showinfo("✓ Repository Valide", result["message"])
            self._update_git_status()
        else:
            messagebox.showerror("✗ Erreur Repository", result["message"])

    def _git_pull(self):
        """Pull du repository"""
        path = self.repo_path.get()
        if not path:
            messagebox.showerror(
                "Erreur", "Veuillez spécifier le chemin du repository")
            return

        # Exécuter en thread pour ne pas bloquer l'UI
        thread = threading.Thread(target=self._git_pull_thread, args=(path,))
        thread.daemon = True
        thread.start()

    def _git_pull_thread(self, path):
        """Thread pour le pull"""
        try:
            result = self.git_manager.pull(path)
            self.root.after(0, lambda: messagebox.showinfo(
                "Pull Réussi", result["message"]))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur Pull", str(e)))
        finally:
            self.root.after(0, self._update_git_status)

    def _git_push(self):
        """Push du repository"""
        path = self.repo_path.get()
        message = self.commit_message.get()

        if not path:
            messagebox.showerror(
                "Erreur", "Veuillez spécifier le chemin du repository")
            return

        if not message:
            messagebox.showerror(
                "Erreur", "Veuillez entrer un message de commit")
            return

        thread = threading.Thread(
            target=self._git_push_thread, args=(path, message))
        thread.daemon = True
        thread.start()

    def _git_push_thread(self, path, message):
        """Thread pour le push"""
        try:
            result = self.git_manager.push(path, message)
            self.root.after(0, lambda: messagebox.showinfo(
                "Push Réussi", result["message"]))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur Push", str(e)))
        finally:
            self.root.after(0, self._update_git_status)

    def _git_status(self):
        """Afficher le statut du repository"""
        path = self.repo_path.get()
        thread = threading.Thread(target=self._git_status_thread, args=(path,))
        thread.daemon = True
        thread.start()

    def _git_status_thread(self, path):
        """Thread pour le statut"""
        try:
            result = self.git_manager.get_status(path)
            self.root.after(0, lambda: self._display_git_status(result))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur Statut", str(e)))

    def _display_git_status(self, status):
        """Afficher le statut dans le textbox"""
        self.git_status_display.configure(state="normal")
        self.git_status_display.delete("1.0", tk.END)
        self.git_status_display.insert("1.0", status["output"])
        self.git_status_display.configure(state="disabled")

    def _git_add_untracked(self):
        """Ajouter tous les fichiers non suivis"""
        path = self.repo_path.get()
        if not path:
            messagebox.showerror(
                "Erreur", "Veuillez spécifier le chemin du repository")
            return

        thread = threading.Thread(
            target=self._git_add_untracked_thread, args=(path,))
        thread.daemon = True
        thread.start()

    def _git_add_untracked_thread(self, path):
        """Thread pour ajouter les fichiers non suivis"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'add', '.'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Succès", "Tous les fichiers non suivis ont été ajoutés"))
                self.logger.log("Fichiers non suivis ajoutés avec succès")
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Erreur", f"Erreur lors de l'ajout: {result.stderr}"))
                self.logger.log(f"Erreur ajout: {result.stderr}")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur", str(e)))
            self.logger.log(f"Erreur: {e}")
        finally:
            self.root.after(0, self._update_git_status)

    def _update_git_status(self):
        """Mettre à jour le statut Git"""
        self._git_status()

    # ======= Méthodes Éditeur =======

    def _on_mousewheel(self, event):
        """Gérer le scroll à la molette de la souris"""
        if event.num == 5 or event.delta < 0:
            # Scroll down
            self.editable_canvas.yview_scroll(3, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            self.editable_canvas.yview_scroll(-3, "units")

    def _get_page_files(self):
        """Récupérer la liste des fichiers HTML disponibles"""
        files = []
        repo_path = Path(self.repo_path.get())

        # Ajouter index.html s'il existe à la racine
        index_file = repo_path / "index.html"
        if index_file.exists():
            files.append("index.html")

        # Ajouter les fichiers du dossier page/
        page_dir = repo_path / "page"
        if page_dir.exists():
            page_files = sorted([f.name for f in page_dir.glob("*.html")])
            files.extend(page_files)

        return files

    def _refresh_files(self):
        """Rafraîchir la liste des fichiers"""
        files = self._get_page_files()
        self.file_combo.configure(values=files)
        messagebox.showinfo("Succès", f"{len(files)} fichiers trouvés")

    def _on_file_selected(self, choice):
        """Charger le fichier sélectionné et afficher les éléments éditables"""
        if not choice:
            return

        repo_path = Path(self.repo_path.get())

        # Vérifier si c'est index.html (à la racine) ou un fichier du dossier page/
        if choice == "index.html":
            file_path = repo_path / "index.html"
        else:
            file_path = repo_path / "page" / choice

        if file_path.exists():
            try:
                # Charger le fichier dans un thread pour ne pas bloquer l'interface
                threading.Thread(target=self._load_file_async, args=(
                    file_path, choice), daemon=True).start()
            except Exception as e:
                messagebox.showerror(
                    "Erreur", f"Impossible de charger le fichier: {e}")
        else:
            messagebox.showerror("Erreur", f"Fichier introuvable: {file_path}")

    def _load_file_async(self, file_path, choice):
        """Charger le fichier de manière asynchrone"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.current_file = file_path
            self.current_file_content = content

            # Extraire les éléments éditables
            result = self.html_manager.extract_editable_elements(content)

            # Planifier l'update dans le thread principal
            self.root.after(0, self._display_editable_elements, result, choice)

        except Exception as e:
            self.logger.log(f"Erreur chargement fichier: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur", f"Erreur lors de la lecture: {e}"))

    def _display_editable_elements(self, result, choice):
        """Afficher les éléments éditables (exécuté dans le thread principal)"""
        # Nettoyer les champs précédents
        for widget in self.editable_scrollframe.winfo_children():
            widget.destroy()
        self.editable_fields = {}

        if result["success"]:
            # Afficher les éléments progressivement par batch
            elements = result["elements"]
            batch_size = 10  # Afficher 10 éléments par batch

            def display_batch(batch_index):
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, len(elements))

                for elem in elements[start_idx:end_idx]:
                    self._create_editable_field(elem)

                # Si il y a d'autres éléments, planifier le batch suivant
                if end_idx < len(elements):
                    self.root.after(50, display_batch, batch_index + 1)
                else:
                    # Tous les éléments sont affichés
                    self.logger.log(
                        f"Fichier ouvert: {choice} ({result['count']} éléments éditables)")
                    messagebox.showinfo(
                        "Succès", f"Fichier chargé: {result['count']} éléments éditables")

            display_batch(0)
        else:
            error_label = ctk.CTkLabel(
                self.editable_scrollframe,
                text=f"⚠️ {result['error']}",
                text_color="orange",
                font=("Montserrat", 11)
            )
            error_label.pack(pady=10, padx=10)
            self.logger.log(f"Aucun élément éditable trouvé dans: {choice}")

    def _create_editable_field(self, elem_info):
        """Créer un champ pour un élément éditable (optimisé)"""
        elem_index = elem_info.get("index", 0)
        elem_id = elem_info.get("id")
        elem_tag = elem_info.get("tag", "unknown")
        is_iframe = elem_info.get("is_iframe", False)
        editable_value = elem_info.get("editable_value", "")

        # Conteneur principal
        field_frame = ctk.CTkFrame(
            self.editable_scrollframe, fg_color="#1e1e1e", corner_radius=10,
            border_width=2, border_color="#404040", width=1600, height=100)
        field_frame.pack(fill=tk.X, padx=12, pady=8)
        field_frame.pack_propagate(False)

        # Info à gauche
        info_frame = ctk.CTkFrame(
            field_frame, fg_color="#252525", corner_radius=8, width=150)
        info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        info_frame.pack_propagate(False)

        # Tag
        tag_label = f"<{elem_tag.upper()}>"
        if is_iframe:
            tag_label += " [SRC]"
        ctk.CTkLabel(
            info_frame,
            text=tag_label,
            text_color="#00D4FF",
            font=("Montserrat", 12, "bold")
        ).pack(anchor="w", padx=8, pady=(8, 2))

        # ID ou index
        id_display = elem_id if elem_id else f"[{elem_index}]"
        ctk.CTkLabel(
            info_frame,
            text=f"#{id_display}",
            text_color="#90EE90",
            font=("Montserrat", 10)
        ).pack(anchor="w", padx=8, pady=(2, 8))

        # Champ de texte à droite
        text_frame = ctk.CTkFrame(field_frame, fg_color="#1e1e1e")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=(0, 10), pady=10)

        text_widget = ctk.CTkTextbox(
            text_frame,
            height=50,
            font=("Montserrat", 14),
            text_color="#FFFFFF",
            fg_color="#2b2b2b",
            corner_radius=6
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Extraire et insérer le contenu
        if is_iframe:
            # Pour les iframes, afficher l'URL du src
            text_widget.insert("1.0", editable_value)
        else:
            # Pour les autres éléments, extraire le texte
            content_html = elem_info.get("content", "")
            soup = BeautifulSoup(content_html, 'html.parser')
            text_content = soup.get_text().strip()
            text_widget.insert("1.0", text_content)

        # Stocker la référence
        self.editable_fields[elem_index] = {
            "widget": text_widget,
            "tag": elem_tag,
            "index": elem_index,
            "is_iframe": is_iframe
        }

    def _save_editable_file(self):
        """Sauvegarder les modifications des éléments éditables"""
        if not self.current_file:
            messagebox.showerror("Erreur", "Aucun fichier sélectionné")
            return

        # Sauvegarder de manière asynchrone
        threading.Thread(target=self._save_file_async, daemon=True).start()

    def _save_file_async(self):
        """Sauvegarder le fichier de manière asynchrone"""
        try:
            content = self.current_file_content
            soup = BeautifulSoup(content, 'html.parser')
            editable_elements = soup.find_all(class_='editable')
            for elem_index, field_info in self.editable_fields.items():
                text_widget = field_info["widget"]
                new_content = text_widget.get("1.0", "end-1c")
                is_iframe = field_info.get("is_iframe", False)
                if isinstance(elem_index, int) and elem_index < len(editable_elements):
                    element = editable_elements[elem_index]
                    if is_iframe:
                        element['src'] = new_content
                        self.logger.log(
                            f"iframe [{elem_index}] src mis à jour: {new_content}")
                    else:
                        element.clear()
                        element.string = new_content
                        self.logger.log(f"Élément [{elem_index}] mis à jour")
            updated_content = str(soup.prettify())
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            self.logger.log(f"Fichier sauvegardé: {self.current_file.name}")

            # Générer automatiquement le sitemap après la sauvegarde
            repo_path = self.repo_path.get()
            sitemap_result = self.sitemap_generator.update_sitemap(repo_path)
            if sitemap_result['success']:
                self.logger.log("Sitemap mis à jour automatiquement")
            else:
                self.logger.log(f"Attention: {sitemap_result['error']}")

            self.root.after(0, lambda: messagebox.showinfo(
                "Succès", f"Fichier sauvegardé: {self.current_file.name}\nSitemap mis à jour automatiquement"))

        except Exception as e:
            self.logger.log(f"Erreur sauvegarde: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur", f"Impossible de sauvegarder: {e}"))

    def _reload_file(self):
        """Recharger le fichier"""
        if self.file_combo.get():
            self._on_file_selected(self.file_combo.get())

    def _update_preview_url(self, event=None):
        """Mettre à jour l'URL de prévisualisation quand le port change"""
        port_str = self.port_entry.get().strip()

        try:
            port = int(port_str)
            # Valider le port
            if 1 <= port <= 65535:
                self.url_label.configure(text=f"http://localhost:{port}")
            else:
                # Fallback : afficher l'URL avec le port par défaut si invalide
                self.url_label.configure(
                    text=f"http://localhost:8000 (⚠️  Port {port} invalide)"
                )
        except ValueError:
            # Fallback : afficher l'URL avec le port par défaut si non numérique
            self.url_label.configure(
                text="http://localhost:8000 (⚠️  Port invalide)")

    # ======= Méthodes Serveur =======

    def _toggle_server(self):
        """Démarrer/arrêter le serveur local"""
        if self.server_running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        """Démarrer le serveur local"""
        try:
            port_str = self.port_entry.get().strip()

            # Valider et convertir le port
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror(
                    "Erreur", "Le port doit être un nombre valide")
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, "8000")
                self._update_preview_url()
                return

            # Vérifier que le port est dans la bonne plage
            if port < 1 or port > 65535:
                messagebox.showerror(
                    "Erreur",
                    f"Le port doit être entre 1 et 65535 (reçu: {port})\n"
                    "Utilisation du port par défaut: 8000"
                )
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, "8000")
                self._update_preview_url()
                return

            repo_path = self.repo_path.get()

            if not Path(repo_path).exists():
                messagebox.showerror(
                    "Erreur", "Le chemin du repository n'existe pas")
                return

            # Démarrer le serveur en thread
            self.server_thread = threading.Thread(
                target=self.server_manager.start,
                args=(repo_path, port, self._on_server_log)
            )
            self.server_thread.daemon = False  # NOT daemon - on veut l'arrêter proprement
            self.server_thread.start()

            self.server_running = True
            self.server_toggle_btn.configure(text="⏹️  Arrêter Serveur")
            self.server_status_label.configure(
                text=f"🟢 Actif (Port {port})", text_color="green")
            self.url_label.configure(text=f"http://localhost:{port}")

            self.logger.log(f"Serveur démarré sur le port {port}")
            messagebox.showinfo(
                "Succès", f"Serveur local démarré sur http://localhost:{port}")

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Impossible de démarrer le serveur: {e}")

    def _stop_server(self):
        """Arrêter le serveur local"""
        try:
            self.server_manager.stop()
            self.server_running = False
            self.server_toggle_btn.configure(text="▶️  Démarrer Serveur")
            self.server_status_label.configure(
                text="⚫ Arrêté", text_color="red")
            self.logger.log("Serveur arrêté")
            messagebox.showinfo("Succès", "Serveur arrêté")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'arrêt: {e}")

    def _on_server_log(self, message):
        """Ajouter un log du serveur"""
        self.root.after(0, lambda: self._append_server_log(message))

    def _append_server_log(self, message):
        """Ajouter le message aux logs du serveur"""
        self.server_logs.configure(state="normal")
        self.server_logs.insert(tk.END, message + "\n")
        self.server_logs.see(tk.END)
        self.server_logs.configure(state="disabled")

    def _open_preview(self):
        """Ouvrir la prévisualisation dans le navigateur"""
        if not self.server_running:
            messagebox.showerror("Erreur", "Le serveur n'est pas actif")
            return

        import webbrowser
        port = self.port_entry.get()
        url = f"http://localhost:{port}"
        webbrowser.open(url)

    # ======= Méthodes Paramètres =======

    def _save_settings(self):
        """Sauvegarder les paramètres"""
        try:
            self.config_manager.set_repo_path(self.default_repo.get())
            self.config_manager.set_auto_pull(self.auto_pull_var.get())
            self.config_manager.set_auto_refresh(self.auto_refresh_var.get())
            self.config_manager.save_config()
            messagebox.showinfo("Succès", "Paramètres sauvegardés")
        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Erreur lors de la sauvegarde: {e}")

    def _reset_settings(self):
        """Réinitialiser les paramètres"""
        self.default_repo.delete(0, tk.END)
        self.default_repo.insert(0, str(Path.home() / "Rout-Art"))
        self.auto_pull_var.set(False)
        self.auto_refresh_var.set(True)

    # ======= Méthodes Logs =======

    def _refresh_logs_display(self):
        """Rafraîchir l'affichage des logs"""
        logs = self.logger.get_logs()
        current_content = self.logs_display.get("1.0", tk.END)
        new_content = "\n".join(logs)

        # Seulement mettre à jour si le contenu a changé
        if current_content != new_content + "\n":
            # Sauvegarder la position du scroll
            was_at_bottom = self.logs_display.yview()[1] >= 0.95

            self.logs_display.configure(state="normal")
            self.logs_display.delete("1.0", tk.END)
            self.logs_display.insert("1.0", new_content)

            # Restaurer le scroll en bas seulement si l'utilisateur était en bas
            if was_at_bottom:
                self.logs_display.see(tk.END)

            self.logs_display.configure(state="disabled")

        # Refresh periodic
        self.root.after(1000, self._refresh_logs_display)

    def _clear_logs(self):
        """Effacer les logs"""
        self.logger.clear_logs()
        self._refresh_logs_display()
        messagebox.showinfo("Succès", "Logs effacés")

    def _export_logs(self):
        """Exporter les logs"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                logs = self.logger.get_logs()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(logs))
                messagebox.showinfo("Succès", f"Logs exportés: {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")

    # ======= Startup =======

    def _on_startup(self):
        """Actions au démarrage"""
        if self.config_manager.get_auto_pull():
            self.logger.log("Pull automatique au démarrage...")
            self._git_pull()


def main():
    """Point d'entrée principal"""
    root = ctk.CTk()
    if getattr(sys, 'frozen', False):
        icon_path = Path(sys._MEIPASS) / 'icon' / 'logo.png'
    else:
        icon_path = Path(__file__).parent / 'icon' / 'logo.png'
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"⚠️  Impossible de charger l'icône: {e}")

    app = MyCMS(root)
    root.mainloop()


if __name__ == "__main__":
    main()
