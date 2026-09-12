let expenses = [];


// OPEN MODAL
function openModal() {
    document.getElementById("expense-modal").classList.add("show");
}


// CLOSE MODAL
function closeModal() {
    document.getElementById("expense-modal").classList.remove("show");
}


// LOAD TRANSACTIONS
async function loadExpenses() {

    const response = await fetch("/api/expenses");

    expenses = await response.json();

    updateDashboard();
}


// ADD TRANSACTION
document.getElementById("expense-form").addEventListener("submit", async function(event) {

    event.preventDefault();

    const title = document.getElementById("title").value;
    const amount = document.getElementById("amount").value;
    const category = document.getElementById("category").value;

    const transactionType = document.querySelector(
        'input[name="transaction-type"]:checked'
    ).value;


    const response = await fetch("/api/expenses", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            title: title,
            amount: amount,
            category: category,
            type: transactionType
        })

    });


    if (response.ok) {

        this.reset();

        closeModal();

        await loadExpenses();

    } else {

        alert("Something went wrong. Please try again.");

    }

});


// DELETE TRANSACTION
async function deleteExpense(id) {

    await fetch(`/api/expenses/${id}`, {
        method: "DELETE"
    });

    await loadExpenses();
}


// UPDATE DASHBOARD
function updateDashboard() {

    updateSummary();

    updateCategories();

    updateTransactions();

    updateChart();

}


// SUMMARY
function updateSummary() {

    let totalIn = 0;
    let totalOut = 0;


    expenses.forEach(expense => {

        const amount = Number(expense.amount);


        if (expense.type === "IN") {

            totalIn += amount;

        } else {

            totalOut += amount;

        }

    });


    const balance = totalIn - totalOut;


    document.getElementById("total-in").textContent =
        "₹" + totalIn.toLocaleString("en-IN");


    document.getElementById("total-out").textContent =
        "₹" + totalOut.toLocaleString("en-IN");


    document.getElementById("balance").textContent =
        "₹" + balance.toLocaleString("en-IN");

}


// CATEGORIES
function updateCategories() {

    const container =
        document.getElementById("category-list");

    container.innerHTML = "";


    let totals = {};


    expenses.forEach(expense => {

        // Only OUT transactions count as spending
        if (expense.type !== "OUT") {
            return;
        }


        if (!totals[expense.category]) {
            totals[expense.category] = 0;
        }


        totals[expense.category] += Number(expense.amount);

    });


    const categories = Object.entries(totals)
        .sort((a, b) => b[1] - a[1]);


    if (categories.length === 0) {

        container.innerHTML =
            '<p class="empty">No spending yet.</p>';

        return;
    }


    categories.forEach(([category, amount]) => {

        const div = document.createElement("div");

        div.className = "category";


        div.innerHTML = `
            <span>
                ${getCategoryIcon(category)}
                ${category}
            </span>

            <strong>
                ₹${amount.toLocaleString("en-IN")}
            </strong>
        `;


        container.appendChild(div);

    });

}


// TRANSACTIONS
function updateTransactions() {

    const container =
        document.getElementById("transaction-list");

    container.innerHTML = "";


    if (expenses.length === 0) {

        container.innerHTML =
            '<p class="empty">No transactions added yet.</p>';

        return;
    }


    expenses.forEach(expense => {

        const div = document.createElement("div");

        div.className = "transaction";


        const isIncome = expense.type === "IN";

        const sign = isIncome ? "+ " : "− ";

        const typeClass = isIncome ? "income" : "expense";


        div.innerHTML = `

            <div>

                <strong>
                    ${escapeHTML(expense.title)}
                </strong>

                <span>
                    ${getCategoryIcon(expense.category)}
                    ${escapeHTML(expense.category)}
                    •
                    ${expense.date}
                </span>

            </div>


            <div class="transaction-right">

                <strong class="${typeClass}">
                    ${sign}₹${Number(expense.amount)
                        .toLocaleString("en-IN")}
                </strong>

                <button
                    class="delete-btn"
                    onclick="deleteExpense(${expense.id})">

                    Delete

                </button>

            </div>

        `;


        container.appendChild(div);

    });

}


// CHART
function updateChart() {

    const chart =
        document.getElementById("chart");

    chart.innerHTML = "";


    // Only OUT transactions are shown as spending activity
    const outgoingExpenses =
        expenses.filter(expense => expense.type === "OUT");


    if (outgoingExpenses.length === 0) {

        chart.innerHTML =
            '<p class="empty">Add OUT transactions to see your spending.</p>';

        return;
    }


    let dailyTotals = {};


    outgoingExpenses.forEach(expense => {

        if (!dailyTotals[expense.date]) {
            dailyTotals[expense.date] = 0;
        }


        dailyTotals[expense.date] += Number(expense.amount);

    });


    const values =
        Object.entries(dailyTotals).slice(-7);


    const max =
        Math.max(...values.map(item => item[1]));


    values.forEach(([date, amount]) => {

        const height =
            max === 0 ? 0 : (amount / max) * 100;


        const bar =
            document.createElement("div");

        bar.className = "bar";

        bar.style.height =
            height + "%";

        bar.title =
            `${date}: ₹${amount}`;


        chart.appendChild(bar);

    });

}


// CATEGORY ICONS
function getCategoryIcon(category) {

    const icons = {

        "Pocket Money": "💰",

        Food: "🍔",

        Transport: "🚕",

        Shopping: "🛍️",

        Education: "📚",

        Entertainment: "🎬",

        Other: "📦"

    };


    return icons[category] || "📦";
}


// SECURITY HELPER
function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


// START APP
loadExpenses();