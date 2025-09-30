document.querySelectorAll(".tableSelectorBtn").forEach(btn => {
    btn.addEventListener("click", async function () {
        const table_placeholder = document.getElementById("tablePlaceHolder")
        const response = await fetch("./get_table_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({"tablename": btn.getAttribute("data-tablename")})
        });

        if (response.ok) {
            table_placeholder.innerHTML = await response.text();
        } else {
            console.log(response.text());
        }
    })
})