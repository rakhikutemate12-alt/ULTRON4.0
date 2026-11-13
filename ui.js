
const ULTRON_UI = {
    elements: {},

    initialize() {
        this.elements = {
            welcome: document.getElementById("welcomeScreen"),
            messages: document.getElementById("messages"),
            input: document.getElementById("messageInput"),
            send: document.getElementById("sendBtn"),
            voice: document.getElementById("voiceBtn"),
            newChat: document.getElementById("newChatBtn"),
            menu: document.getElementById("menuBtn"),
            sidebar: document.getElementById("sidebar")
        };
    },

    // Safely render inline Markdown.
    renderInline(text, container) {
        const pattern = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\*\*([^*]+)\*\*/g;

        let lastIndex = 0;
        let match;

        while ((match = pattern.exec(text)) !== null) {
            // Add normal text before the match.
            if (match.index > lastIndex) {
                container.appendChild(
                    document.createTextNode(
                        text.slice(lastIndex, match.index)
                    )
                );
            }

            if (match[2]) {
                // Validate links before creating clickable elements.
                try {
                    const url = new URL(match[2]);

                    if (url.protocol === "http:" || url.protocol === "https:") {
                        const link = document.createElement("a");
                        link.textContent = match[1];
                        link.href = url.href;
                        link.target = "_blank";
                        link.rel = "noopener noreferrer";
                        link.className = "ultron-article-link";

                        container.appendChild(link);
                    } else {
                        container.appendChild(
                            document.createTextNode(match[1])
                        );
                    }
                } catch {
                    container.appendChild(
                        document.createTextNode(match[1])
                    );
                }
            } else if (match[3]) {
                const bold = document.createElement("strong");
                bold.textContent = match[3];
                container.appendChild(bold);
            }

            lastIndex = pattern.lastIndex;
        }

        // Add remaining normal text.
        if (lastIndex < text.length) {
            container.appendChild(
                document.createTextNode(text.slice(lastIndex))
            );
        }
    },

    // Render Markdown blocks without using unsafe HTML.
    renderMarkdown(content, container) {
        const lines = content.replace(/\r\n/g, "\n").split("\n");

        let paragraphLines = [];

        const flushParagraph = () => {
            if (paragraphLines.length === 0) return;

            const paragraph = document.createElement("p");
            paragraph.className = "ultron-paragraph";

            paragraphLines.forEach((line, index) => {
                if (index > 0) {
                    paragraph.appendChild(
                        document.createElement("br")
                    );
                }

                this.renderInline(line, paragraph);
            });

            container.appendChild(paragraph);
            paragraphLines = [];
        };

        lines.forEach(line => {
            const trimmed = line.trim();

            // Empty line: finish current paragraph.
            if (!trimmed) {
                flushParagraph();
                return;
            }

            // Markdown horizontal rule.
            if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
                flushParagraph();

                const divider = document.createElement("hr");
                divider.className = "ultron-divider";
                container.appendChild(divider);
                return;
            }

            // Markdown headings.
            const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);

            if (headingMatch) {
                flushParagraph();

                const level = headingMatch[1].length;
                const heading = document.createElement(`h${level}`);
                heading.className = "ultron-heading";

                this.renderInline(headingMatch[2], heading);
                container.appendChild(heading);
                return;
            }

            paragraphLines.push(line);
        });

        flushParagraph();
    },

    addMessage(role, content) {
        this.elements.welcome.style.display = "none";

        const message = document.createElement("div");
        message.className = `message ${role}`;

        const label = document.createElement("span");
        label.className = "message-label";
        label.textContent = role === "user" ? "YOU" : "ULTRON";

        const text = document.createElement("div");
        text.className = "message-content";

        if (role === "assistant") {
            this.renderMarkdown(content, text);
        } else {
            // User messages remain plain text.
            text.textContent = content;
        }

        message.append(label, text);
        this.elements.messages.appendChild(message);

        this.scrollToBottom();
    },

    showLoading() {
        const loading = document.createElement("div");
        loading.className = "message assistant";
        loading.id = "ultronLoading";
        loading.textContent = "ULTRON is thinking...";

        this.elements.messages.appendChild(loading);
        this.scrollToBottom();
    },

    hideLoading() {
        document.getElementById("ultronLoading")?.remove();
    },

    scrollToBottom() {
        const area = document.getElementById("chatArea");

        if (area) {
            area.scrollTop = area.scrollHeight;
        }
    },

    resetChat() {
        this.elements.messages.replaceChildren();
        this.elements.welcome.style.display = "block";
        this.elements.input.value = "";
    },

    setBusy(busy) {
        this.elements.send.disabled = busy;
        this.elements.send.style.opacity = busy ? "0.5" : "1";
    }
};

window.ULTRON_UI = ULTRON_UI;
