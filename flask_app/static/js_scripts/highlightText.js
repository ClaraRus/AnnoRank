function highlightText() {
    const queryElement = document.getElementById('query_info');
    if (!queryElement) return;

    const queryTokens = queryElement.textContent
        .replace(/\s+/g, ' ')
        .trim()
        .split(' ')
        .filter(t => t.length > 0);

    const tr_list = document.getElementsByTagName('tr');

    for (let tr of tr_list) {
        const td_list = tr.getElementsByTagName('td');

        for (let td of td_list) {
            if (
                td.querySelector('button') ||
                td.querySelector('input[type="checkbox"]') ||
                td.querySelector('a')
            ) continue;

            walkTextNodes(td, (textNode) => {
                const parent = textNode.parentNode;
                let original = textNode.nodeValue;
                let segments = [original];

                queryTokens.forEach(token => {
                    segments = segments.flatMap(segment => {
                        if (typeof segment !== 'string') return [segment]; // already processed

                        const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(`\\b(${escaped})\\b`, 'gi');
                        const parts = segment.split(regex);

                        return parts.map(part => {
                            if (part.toLowerCase() === token.toLowerCase()) {
                                const span = document.createElement('span');
                                span.style.fontWeight = 'bold';
                                span.textContent = part;
                                return span;
                            } else {
                                return part;
                            }
                        });
                    });
                });

                if (segments.length > 1) {
                    segments.forEach(s => {
                        if (typeof s === 'string') {
                            parent.insertBefore(document.createTextNode(s), textNode);
                        } else {
                            parent.insertBefore(s, textNode);
                        }
                    });
                    parent.removeChild(textNode);
                }
            });
        }
    }

    // Recursively walk text nodes
    function walkTextNodes(node, callback) {
        const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null, false);
        let current;
        while (current = walker.nextNode()) {
            callback(current);
        }
    }
}
