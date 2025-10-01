document.querySelectorAll(".tableSelectorBtn").forEach(btn => {
    btn.addEventListener("click", async function () {
        const tablePlaceHolder = document.getElementById("tablePlaceHolder");
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
                // привязываем необходимые элементы
                const modalBackground = document.getElementsByClassName("modalBackground")[0];
                const modalClose = document.getElementsByClassName("modalClose")[0];
                const modalWindow = document.getElementsByClassName("modalWindow")[0];
                // функция для корректировки положения body при появлении ползунка прокрутки
                // событие нажатия на триггер открытия модального окна
                trigger.addEventListener("click", async function () {
                    // делаем модальное окно видимым
                    modalBackground.style.display = "block";
                    const response = await fetch("./get_table_row", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({"id": trigger.getAttribute("data-card-id"), "tablename": btn.getAttribute("data-tablename")})
                    });

                    if (response.ok) {
                        modalWindow.innerHTML = await response.text();
                        modalWindow.setAttribute("data-tablename", btn.getAttribute("data-tablename"))
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

async function modalSaveOnClick(row_id) {
    const modalBackground = document.getElementsByClassName("modalBackground")[0];
    const modalWindow = document.getElementsByClassName("modalWindow")[0];
    var dataToSave = {};
    modalWindow.querySelectorAll("label").forEach(label => {
        var labelText = label.childNodes[0].textContent.trim();
        var textArea = label.querySelector("textarea").value;
        dataToSave[labelText] = textArea;
    })
    console.log(dataToSave);
    const response = await fetch("./save_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"id": row_id, "tablename": modalWindow.getAttribute("data-tablename"), "data": dataToSave})
    });

    if (response.ok) {
        modalBackground.style.display = "none";
    } else {
        console.log(response.text());
    }
}

async function modalCreateOnClick() {
    
}