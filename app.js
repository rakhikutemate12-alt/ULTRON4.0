document.addEventListener("DOMContentLoaded", () => {

    // 1. Initialize interface
    ULTRON_UI.initialize();

    // 2. Restore saved conversation history
    ULTRON_CHAT.restoreHistory();

    // 3. Load saved settings
    ULTRON_SETTINGS.loadSettings();

    // 4. Initialize voice recognition
    ULTRON_VOICE.initialize();

    // 5. Send message button
    ULTRON_UI.elements.send.addEventListener("click", () => {
        ULTRON_CHAT.sendMessage(
            ULTRON_UI.elements.input.value
        );
    });

    // 6. Enter key sends message
    ULTRON_UI.elements.input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();

            ULTRON_CHAT.sendMessage(
                ULTRON_UI.elements.input.value
            );
        }
    });

    // 7. Start a new conversation
    ULTRON_UI.elements.newChat.addEventListener("click", () => {
        ULTRON_CHAT.newChat();
    });

    // 8. Voice button
    ULTRON_UI.elements.voice.addEventListener("click", () => {
        ULTRON_VOICE.start();
    });

    // 9. Mobile sidebar menu
    ULTRON_UI.elements.menu.addEventListener("click", () => {
        ULTRON_UI.elements.sidebar.classList.toggle("open");
    });

    // 10. Suggested prompts
    document.querySelectorAll(".suggestion-card").forEach((card) => {
        card.addEventListener("click", () => {
            const prompt =
                card.dataset.prompt || card.textContent.trim();

            ULTRON_CHAT.sendMessage(prompt);
        });
    });

    // 11. Check backend connection
    ULTRON_API.checkHealth()
        .then(() => {
            console.log("ULTRON backend connected.");
        })
        .catch((error) => {
            console.error("Backend connection failed:", error);
        });

    console.log("ULTRON AI 4.0 initialized successfully.");
});