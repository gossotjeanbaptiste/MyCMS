# 📋 Intégration Sitemap Automatique

## 🎯 Objectif
Générer automatiquement le `sitemap.xml` avec les **vraies dates de modification** des fichiers HTML, sans intervention manuelle.

## 🏗️ Architecture

### Nouveau Module: `sitemap_generator.py`
Classe `SitemapGenerator` qui :
- ✅ Détecte automatiquement les fichiers HTML du projet
- ✅ Récupère la **date réelle de modification** de chaque fichier (via `st_mtime`)
- ✅ Génère le XML selon le standard des sitemaps
- ✅ Sauvegarde automatiquement dans `sitemap.xml`

### Configuration des Pages
Chaque page a une priorité et fréquence configurées :
```python
"page/formations.html": {"changefreq": "monthly", "priority": 0.9}
```

## 🔄 Intégration au CMS

### Modifications dans `rout_art_cms.py`

1. **Import du module**
```python
from sitemap_generator import SitemapGenerator
```

2. **Initialisation dans `__init__`**
```python
self.sitemap_generator = SitemapGenerator(self.logger)
```

3. **Appel automatique après sauvegarde** (dans `_save_file_async`)
```python
# Générer automatiquement le sitemap après la sauvegarde
repo_path = self.repo_path.get()
sitemap_result = self.sitemap_generator.update_sitemap(repo_path)
```

## 🚀 Fonctionnement

### Workflow Utilisateur
1. L'utilisateur édite une page via le CMS
2. L'utilisateur clique "Sauvegarder"
3. Le fichier HTML est sauvegardé
4. **Automatiquement** → Le sitemap est régénéré avec les vraies dates
5. L'utilisateur reçoit une confirmation

### Dates Utilisées
- **Avant** : dates manuelles (2025-10-06) stagnantes
- **Après** : dates réelles de modification des fichiers via le système d'exploitation

## 📁 Fichiers Modifiés/Créés

```
cms/source/
├── sitemap_generator.py       ✨ NOUVEAU
└── rout_art_cms.py            📝 MODIFIÉ (imports + initialisation + appel)
```

## 🧪 Test

Exécuter le script de test :
```bash
python test_sitemap.py
```

Cela va :
1. Générer un nouveau sitemap
2. Afficher les dates réelles des fichiers
3. Sauvegarder dans `sitemap.xml`

## 📊 Résultat Attendu

Le sitemap généré contiendra :
```xml
<url>
    <loc>https://autoecoleroutart.github.io/page/formations.html</loc>
    <lastmod>2025-12-03</lastmod>  <!-- Date réelle du fichier -->
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
</url>
```

## ✅ Avantages

1. **Automatique** - Plus besoin de mises à jour manuelles
2. **Fiable** - Utilise les vraies dates du système
3. **SEO-Friendly** - Google crawle les pages au bon moment
4. **Maintenable** - Centralisé dans un seul module

## ⚠️ Notes

- Le sitemap ne met pas à jour `template.html` (fichier exclu)
- Les dates sont au format ISO (YYYY-MM-DD)
- Le sitemap suit le standard XML officiel
