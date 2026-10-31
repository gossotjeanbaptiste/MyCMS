// MyCMS - interroger le serveur à intervalle régulier, seulement quand c'est utile :
// tant que active() est vrai (onglet ouvert, serveur lancé…) et que la fenêtre est visible.

// tick : une interrogation ; active : faut-il continuer. Retourne { start, stop }
export function createPoller(interval, tick, active) {
    const poller = { timer: null };

    async function run() {
        if (!active() || document.hidden) return; // Arrêté, ou en pause jusqu'au retour sur la fenêtre
        try {
            await tick();
        } catch {
            return; // Serveur injoignable ou session expirée : on n'insiste pas
        }
        schedule();
    }

    function schedule() {
        clearTimeout(poller.timer);
        if (active()) poller.timer = setTimeout(run, interval);
    }

    // Retour sur la fenêtre : rattraper tout de suite, puis reprendre le rythme
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden && active()) {
            clearTimeout(poller.timer);
            run();
        }
    });

    return { start: schedule, stop: () => clearTimeout(poller.timer) };
}
