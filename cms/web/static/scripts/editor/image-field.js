// MyCMS - carte d'une image éditable (<img class="editable">) : vignette, adresse, choix d'une nouvelle image

import { api, element, toast } from "../core/dom.js";
import { state } from "../core/state.js";

const ACCEPTED = "image/png,image/jpeg,image/gif,image/webp,image/avif";

function thumbnailUrl(src) {
    return `/api/site-image?page=${encodeURIComponent(state.editor.file)}&src=${encodeURIComponent(src)}`;
}

// Vignette de l'image : celle du site, ou un message si elle est introuvable (adresse externe, fichier absent)
function updateThumbnail(thumbnail, missing, src) {
    thumbnail.classList.toggle("hidden", !src);
    missing.classList.add("hidden");
    if (src) thumbnail.src = thumbnailUrl(src);
}

// Envoyer l'image choisie : elle est copiée dans le dossier images/ du site, son adresse remplace l'ancienne
async function upload(file, input) {
    const form = new FormData();
    form.append("page", state.editor.file);
    form.append("file", file);
    const result = await api("POST", "/api/images", form);
    input.value = result.src;
    // Même chemin qu'une saisie : la carte devient modifiée (voir input.js)
    input.dispatchEvent(new Event("input", { bubbles: true }));
    toast(`Image ajoutée au site : ${result.path}. Sauvegardez pour l'utiliser dans la page.`);
}

// Retourne { control, input } : input porte l'adresse (src), comme le champ d'une iframe
export function buildImageField(elem) {
    const control = element("div", "flex flex-wrap items-start gap-3");
    const thumbnail = element("img", "max-h-32 max-w-48 rounded-md border border-line bg-white object-contain");
    thumbnail.alt = "Aperçu de l'image";
    const missing = element("p", "hidden py-2 text-muted", "Aperçu indisponible (image externe ou introuvable).");
    thumbnail.addEventListener("error", () => {
        thumbnail.classList.add("hidden");
        missing.classList.remove("hidden");
    });

    const side = element("div", "flex min-w-48 flex-1 flex-col gap-2");
    const input = element("input", "input w-full font-mono text-xs");
    input.value = elem.value;
    input.spellcheck = false;
    input.setAttribute("aria-label", "Adresse de l'image");
    input.addEventListener("input", () => updateThumbnail(thumbnail, missing, input.value.trim()));

    const picker = element("input", "hidden");
    picker.type = "file";
    picker.accept = ACCEPTED;
    const choose = element("button", "btn self-start", "Choisir une image…");
    choose.type = "button";
    choose.addEventListener("click", () => picker.click());
    picker.addEventListener("change", async () => {
        const file = picker.files[0];
        picker.value = "";
        if (!file) return;
        choose.disabled = true;
        try {
            await upload(file, input);
        } catch (e) {
            toast(e.message, true);
        } finally {
            choose.disabled = false;
        }
    });

    side.append(input, choose, picker);
    control.append(thumbnail, missing, side);
    updateThumbnail(thumbnail, missing, elem.value);
    return { control, input };
}
