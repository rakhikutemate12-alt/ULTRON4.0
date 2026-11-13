
const ULTRON_SETTINGS = {
    language: "en",
    theme: "dark",

    setLanguage(language) {
        this.language = language;
        localStorage.setItem("ultron_language", language);
    },

    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("ultron_theme", theme);
    },

    loadSettings() {
        this.language =
            localStorage.getItem("ultron_language") || "en";

        this.theme =
            localStorage.getItem("ultron_theme") || "dark";

        document.documentElement.setAttribute(
            "data-theme",
            this.theme
        );
    }
};

window.ULTRON_SETTINGS = ULTRON_SETTINGS;
