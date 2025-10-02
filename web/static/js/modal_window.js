async function modalSaveOnClick(row_id) {
    const modalBackground = document.getElementsByClassName("modalBackground")[0];
    const modalWindow = document.getElementsByClassName("modalWindow")[0];
    var dataToSave = {};
    modalWindow.querySelectorAll("label").forEach(label => {
        var labelText = label.childNodes[0].textContent.trim();
        var textArea = label.querySelector("textarea").value;
        dataToSave[labelText] = textArea;
    })

    const response = await fetch("./save_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"id": row_id, "tablename": modalWindow.tableName, "data": dataToSave})
    });

    if (response.ok) {
        modalBackground.style.display = "none";
        // --- обновляем строку таблицы ---
        const table = document.getElementById("tablePlaceHolder");
        const thead = table.querySelector("thead");
        const tbody = table.querySelector("tbody");

        // ищем строку с нужной кнопкой
        const row = tbody.querySelector(`tr[data-row-id="${row_id}"]`);
        if (row) {
            const headers = Array.from(thead.querySelectorAll("th")).slice(1); // кроме кнопки
            headers.forEach((th, index) => {
                const colName = th.textContent.trim();
                if (dataToSave[colName] !== undefined) {
                    row.cells[index + 1].textContent = dataToSave[colName];
                }
            });
        }
    } else {
        console.log(response.text());
    }
}

async function modalCreateOnClick() {
    const modalBackground = document.getElementsByClassName("modalBackground")[0];
    const modalWindow = document.getElementsByClassName("modalWindow")[0];
    var dataToSave = {};
    modalWindow.querySelectorAll("label").forEach(label => {
        var labelText = label.childNodes[0].textContent.trim();
        var textArea = label.querySelector("textarea").value;
        dataToSave[labelText] = textArea;
    })
    const response = await fetch("./create_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"tablename": modalWindow.tableName, "data": dataToSave})
    });

    if (response.ok) {
        const response_json = await response.json();
        dataToSave["ИД"] = response_json['id'];
        modalBackground.style.display = "none";
        const tbody = document.getElementById("tablePlaceHolder").querySelector("tbody");
        const thead = document.getElementById("tablePlaceHolder").querySelector("thead");
        var newRow = tbody.insertRow();
        var btn_cell = newRow.insertCell(0);
        btn_cell.innerHTML = `<button class="btn trigger" data-card-id="${response_json['id']}">Подробнее</button>`;
        Array.from(thead.querySelectorAll("th")).slice(1).forEach( th => {
            var newCell = newRow.insertCell();
            newCell.textContent = dataToSave[th.textContent] ?? ""
        })
    } else {
        console.log(await response.text());
    }
}

async function modalDeleteOnClick(row_id) {
    const modalBackground = document.getElementsByClassName("modalBackground")[0];
    const modalWindow = document.getElementsByClassName("modalWindow")[0];
    const response = await fetch("./delete_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"tablename": modalWindow.tableName, "id": row_id})
    });

    if (response.ok) {
        modalBackground.style.display = "none";
        const row = document.getElementById("tablePlaceHolder").querySelector(`tr[data-row-id="${row_id}"]`);
        row.remove();
    } else {
        console.log(await response.text());
    }
}
