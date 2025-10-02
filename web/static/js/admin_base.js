function openModal(innerHTML, tableName) {
    const modalBackground = document.getElementsByClassName("modalBackground")[0];
    const modalClose = document.getElementsByClassName("modalClose")[0];
    const modalWindow = document.getElementsByClassName("modalWindow")[0];
    // делаем модальное окно видимым
    modalBackground.style.display = "block";
    modalWindow.innerHTML = innerHTML;
    modalWindow.tableName = tableName;
    // нажатие на крестик закрытия модального окна
    modalClose.addEventListener("click", function () {
        modalBackground.style.display = "none";
    });
    modalBackground.addEventListener("click", function (event) {
        if (event.target === modalBackground) {
            modalBackground.style.display = "none";
        }
    });
}

async function openModalToCreateRow(tableName) {
    const response = await fetch("./get_modal_to_create_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"tablename": tableName})
    });

    if (response.ok) {
        openModal(await response.text(), tableName)
    } else {
        console.log(await response.text());
    }
};


async function openModalToSaveRow(rowId, tableName) {
    console.log(`openModalToSaveRow ${rowId} ${tableName}`)
    const response = await fetch("./get_table_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"id": rowId, "tablename": tableName})
    });

    if (response.ok) {
        openModal(await response.text(), tableName)
    } else {
        console.log(response.text());
    }
};


async function fillTable(tableName) {
    const tablePlaceHolder = document.getElementById("tablePlaceHolder");
    const response = await fetch("./get_table_data", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"tablename": tableName})
    });

    if (response.ok) {
        tablePlaceHolder.innerHTML = await response.text();
    } else {
        console.log(response.text());
    }
}
