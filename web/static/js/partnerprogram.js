document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".category").forEach( card => {
        var category_id = Number(card.getAttribute("data-category-id"));
        card.addEventListener("click", async function (event) {
        window.location.href = `./cards?category_id=${category_id}`
        })
    })
})