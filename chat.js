
const ULTRON_CHAT = {
    history: [],
    busy: false,

    setVisualState(state) {
        if (window.ULTRON_3D) {
            window.ULTRON_3D.setState(state);
        }
    },

    restoreHistory() {
        try {
            const saved = ULTRON_MEMORY.load();

            if (!Array.isArray(saved)) {
                this.history = [];
                return;
            }

            this.history = saved
                .filter(item =>
                    item &&
                    ["user", "assistant"].includes(item.role) &&
                    typeof item.content === "string" &&
                    item.content.trim().length > 0 &&
                    item.content.length <= 4000
                )
                .slice(-20);

            if (this.history.length === 0) return;

            ULTRON_UI.elements.welcome.style.display = "none";

            this.history.forEach(item => {
                ULTRON_UI.addMessage(item.role, item.content);
            });

        } catch (error) {
            console.error("History restore error:", error);
            this.history = [];
        }
    },

    saveHistory() {
        ULTRON_MEMORY.save(this.history.slice(-20));
    },

    async sendMessage(message) {
        if (this.busy) return;
        if (typeof message !== "string") return;

        message = message.trim();
        if (!message) return;

        if (message.length > 4000) {
            ULTRON_UI.addMessage("assistant", "Your message is too long.");
            return;
        }

        this.busy = true;
        this.setVisualState("thinking");
        ULTRON_UI.setBusy(true);

        this.history.push({
            role: "user",
            content: message
        });

        this.history = this.history.slice(-20);
        this.saveHistory();

        ULTRON_UI.addMessage("user", message);
        ULTRON_UI.elements.input.value = "";
        ULTRON_UI.showLoading();

        let fullReply = "";

        try {
            const reply = await ULTRON_API.sendMessageStream(
                this.history,
                token => {
                    fullReply += token;
                }
            );

            fullReply = reply || fullReply;

            ULTRON_UI.hideLoading();

            if (!fullReply.trim()) {
                throw new Error("ULTRON could not generate a response.");
            }

            ULTRON_UI.addMessage("assistant", fullReply);

            this.history.push({
                role: "assistant",
                content: fullReply
            });

            this.history = this.history.slice(-20);
            this.saveHistory();

            if (window.ULTRON_VOICE &&
                typeof ULTRON_VOICE.speak === "function") {
                ULTRON_VOICE.speak(fullReply);
            }

        } catch (error) {
            ULTRON_UI.hideLoading();

            console.error("ULTRON chat error:", error);

            ULTRON_UI.addMessage(
                "assistant",
                error.message || "ULTRON could not respond."
            );

        } finally {
            ULTRON_UI.hideLoading();
            this.busy = false;
            ULTRON_UI.setBusy(false);
            this.setVisualState("idle");
            ULTRON_UI.elements.input.focus();
        }
    },

    newChat() {
        if (this.busy) return;

        this.history = [];
        ULTRON_MEMORY.clear();
        ULTRON_UI.resetChat();
        this.setVisualState("idle");
    }
};

window.ULTRON_CHAT = ULTRON_CHAT;
