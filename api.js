
const ULTRON_API = {
    baseURL: "/api",

    async sendMessage(messages) {
        const response = await fetch(`${this.baseURL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ messages })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "ULTRON could not respond.");
        }

        return data.reply;
    },

    async sendMessageStream(messages, onToken) {
        const response = await fetch(`${this.baseURL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages,
                stream: true
            })
        });

        if (!response.ok) {
            let error = "ULTRON could not respond.";

            try {
                const data = await response.json();
                error = data.error || error;
            } catch (_) {}

            throw new Error(error);
        }

        if (!response.body) {
            throw new Error("Streaming is not supported by this browser.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullReply = "";

        try {
            while (true) {
                const { value, done } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.trim()) continue;

                    const data = JSON.parse(line);

                    if (data.error) {
                        throw new Error(data.error);
                    }

                    if (data.token) {
                        fullReply += data.token;
                        onToken(data.token);
                    }

                    if (data.done) {
                        return fullReply;
                    }
                }
            }

            if (buffer.trim()) {
                const data = JSON.parse(buffer);

                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.token) {
                    fullReply += data.token;
                    onToken(data.token);
                }
            }

            return fullReply;

        } finally {
            reader.releaseLock();
        }
    },

    async checkHealth() {
        const response = await fetch(`${this.baseURL}/health`);

        if (!response.ok) {
            throw new Error("Backend is not responding.");
        }

        return response.json();
    }
};

window.ULTRON_API = ULTRON_API;
