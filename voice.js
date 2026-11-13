
const ULTRON_VOICE = {
    recognition: null,
    listening: false,
    speaking: false,
    language: "en-IN",

    initialize() {
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.lang = this.language;
            this.recognition.continuous = false;
            this.recognition.interimResults = false;

            this.recognition.onresult = (event) => {
                const transcript =
                    event.results[0][0].transcript;

                ULTRON_UI.elements.input.value = transcript;
                ULTRON_CHAT.sendMessage(transcript);
            };

            this.recognition.onend = () => {
                this.listening = false;
            };

            this.recognition.onerror = (event) => {
                console.error("Voice error:", event.error);
                this.listening = false;
            };
        }

        return true;
    },

    start() {
        if (!this.recognition) {
            alert("Voice recognition is not supported in this browser.");
            return;
        }

        if (this.listening) return;

        try {
            this.recognition.start();
            this.listening = true;
        } catch (error) {
            console.error(error);
        }
    },

    stop() {
        if (this.recognition && this.listening) {
            this.recognition.stop();
            this.listening = false;
        }
    },

    speak(text) {
        if (!("speechSynthesis" in window)) {
            console.warn("Speech output is not supported.");
            return;
        }

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        utterance.lang = this.language;
        utterance.rate = 1;
        utterance.pitch = 0.9;
        utterance.volume = 1;

        utterance.onstart = () => {
            this.speaking = true;
        };

        utterance.onend = () => {
            this.speaking = false;
        };

        utterance.onerror = () => {
            this.speaking = false;
        };

        window.speechSynthesis.speak(utterance);
    },

    stopSpeaking() {
        window.speechSynthesis.cancel();
        this.speaking = false;
    },

    setLanguage(language) {
        this.language = language;

        if (this.recognition) {
            this.recognition.lang = language;
        }
    }
};

window.ULTRON_VOICE = ULTRON_VOICE;
