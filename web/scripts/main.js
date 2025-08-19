document.addEventListener("DOMContentLoaded", function (event) {
    let platforms = [];
    let color = {};
    let font = {};

    fetch('init')
        .then((response) => response.json())
        .then((data) => init(data));

    const socket = () => {
        const ws = new WebSocket(`ws://localhost:6660/ws`);

        ws.onopen = () => {
        };

        ws.onmessage = (event) => {
            let _data = JSON.parse(event.data);
            init(_data);
        };

        ws.onclose = (e) => {
            setTimeout(() => {
                socket();
            }, 5000);
        };

        ws.onerror = (err) => {
            ws.close();
        };
    }

    socket();

    const init = (_data) => {
        platforms = Object.values(_data.platforms).sort((a, b) => a.position - b.position)

        color = _data.color;
        font = _data.font;

        update();
    }

    const update = () => {
        const main = document.getElementById("main");
        main.textContent = "";

        const ul = document.createElement("ul");

        for (const platform of platforms) {
            const li = document.createElement("li");
            li.classList.add("default");
            li.style.color = color.default;

            if (platform.current) {
                li.classList.add("current");
                li.style.color = color.current;
            }

            if (!platform.count) {
                li.classList.add("end");
                li.style.color = color.end;
            }

            const title = document.createTextNode(platform.title);
            li.appendChild(title);

            if (platform.count > 1) {
                li.appendChild(document.createElement("br"));

                const count = document.createTextNode("x" + platform.count);
                li.appendChild(count);
            }

            ul.appendChild(li);
        }

        main.appendChild(ul);

        console.log(font)

        main.style.fontFamily = `${font.family}, serif`;
        main.style.fontWeight = `${font.weight}`;
        main.style.fontStyle = `${font.italic ? 'italic' : 'normal'}`;
    }
});

