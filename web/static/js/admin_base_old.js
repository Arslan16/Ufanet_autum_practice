document.querySelectorAll(".tableSelectorBtn").forEach(btn => {
    btn.addEventListener("click", async function () {
        const tablePlaceHolder = document.getElementById("tablePlaceHolder")
        const response = await fetch("./get_table_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({"tablename": btn.getAttribute("data-tablename")})
        });

        if (response.ok) {
            tablePlaceHolder.innerHTML = await response.text();
            const tableContainer = document.getElementById("tableContainer");
            tableContainer.querySelector("tbody").querySelectorAll(".trigger").forEach(trigger => {
                // получаем ширину отображенного содержимого и толщину ползунка прокрутки
                const windowInnerWidth = document.documentElement.clientWidth;
                const scrollbarWidth = parseInt(window.innerWidth) - parseInt(windowInnerWidth);

                // привязываем необходимые элементы
                const modalBackground = document.getElementsByClassName("modalBackground")[0];
                const modalClose = document.getElementsByClassName("modalClose")[0];
                const modalActive = document.getElementsByClassName("modalActive")[0];
                const modalWindow = document.getElementsByClassName("modalWindow")[0];
                // событие нажатия на триггер открытия модального окна
                trigger.addEventListener("click", async function () {
                    // делаем модальное окно видимым
                    modalBackground.style.display = "block";
                    // позиционируем наше окно по середине, где 175 - половина ширины модального окна
                    modalActive.style.left = "calc(50% - " + (175 - scrollbarWidth / 2) + "px)";
                    const response = await fetch(window.location.pathname + "get_card_info", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({"card_id": trigger.getAttribute("data-card-id")})
                    });

                    if (response.ok) {
                        modalWindow.innerHTML = await response.text();
                    } else {
                        console.log(response.text());
                    }
                });

                // нажатие на крестик закрытия модального окна
                modalClose.addEventListener("click", function () {
                    modalBackground.style.display = "none";
                });

                // закрытие модального окна на зону вне окна, т.е. на фон
                modalBackground.addEventListener("click", function (event) {
                    if (event.target === modalBackground) {
                        modalBackground.style.display = "none";
                    }
                });
            })
        } else {
            console.log(response.text());
        }
    })
})