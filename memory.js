
const ULTRON_MEMORY = {
    storageKey: "ultron_chat_history",

    save(history) {
        try {
            localStorage.setItem(
                this.storageKey,
                JSON.stringify(history)
            );

            return true;
        } catch (error) {
            console.error("Memory save failed:", error);
            return false;
        }
    },

    load() {
        try {
            const saved = localStorage.getItem(this.storageKey);

            if (!saved) return [];

            const history = JSON.parse(saved);

            return Array.isArray(history) ? history : [];

        } catch (error) {
            console.error("Memory load failed:", error);
            return [];
        }
    },

    clear() {
        localStorage.removeItem(this.storageKey);
    }
};

window.ULTRON_MEMORY = ULTRON_MEMORY;
