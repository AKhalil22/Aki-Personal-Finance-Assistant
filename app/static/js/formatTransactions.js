// Wait for DOM (Document Object Model) to fully load
document.addEventListener('DOMContentLoaded', function() {
    // Fetch transaction button & list element
    const addTransactionButton = document.querySelector(".add-transaction-button");
    const transactionList = document.querySelector(".transaction-list");

    // Function/Event listener to handle transaction creation
    addTransactionButton.addEventListener("click", () => {
        // Create a new <li> element
        const newTransaction = document.createElement("li");
        newTransaction.classList.add("transaction-item");

        // Create unique ID via timestamp created
        const uniqueId = `transaction-${Date.now()}`;
        newTransaction.setAttribute("data-id", uniqueId);

        newTransaction.innerHTML = `
            <div class="transaction-details">
                <div class="transaction-title-container">
                    <span class="transaction-title" data-id="${uniqueId}"
                        ondblclick="editField(event, 'description')">New Transaction</span>

                    <button class="delete-button">Delete</button>
                </div>
                <span class="transaction-date" data-id="${uniqueId}" ondblclick="editField(event, 'date')">${new Date().toLocaleDateString()}</span>
            </div>
            <div class="transaction-amount">
                <button class="transaction-category" data-id="${uniqueId}" ondblclick="editField(event, 'category')">Category</button>
                <!-- Use formatNumber function to format money -->
                <span class="amount" data-id="${uniqueId}" ondblclick="editField(event, 'amount')">$0.00</span>
            </div>
        `;

        // Append the transaction to the list
        transactionList.appendChild(newTransaction);

        // Debug:
        console.log(`Transaction added with ID: ${uniqueId}`);
    });

    // Function to handle deletion of transactions
    transactionList.addEventListener("click", (event) => {
        if (event.target.classList.contains("delete-button")) {

            // Fetch item user wishes to delete
            const transactionItemId = event.target.dataset.id;
            const transactionTitle = document.querySelector(`.transaction-title[data-id="${transactionItemId}"]`)
            console.log("Deletion from event:", transactionItemId);

            // Confirm deletion
            if (window.confirm("Permanently Delete:", transactionTitle)) {
                deleteTransaction(transactionItem.dataset.id)
                transactionItem.remove();
                console.log(`Transaction deleted with ID: ${transactionItem.dataset.id}`)
            }
        }
    });

    // Function to handle deletion of transaction
    function deleteTransaction(transactionId) {
        const data = {
            id: transactionId
        };

        fetch('/delete_transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Transaction deleted:", data);
        })
        .catch((error) => {
            console.error("Error:", error);
        });
    }


    // Function to handle the editing of fields
    window.editField = function(event, field) {
        // event.target = Get Element Cicked
        const originalValue = event.target.textContent.trim(); // Removes any whitespace
        const transactionId = event.target.dataset.id; // dataset =  provides access to all the data-* attributes | id = refers to the specific data-id

        let inputElement;

        // Depending on field, create input element
        if (field === 'amount') {
            // amount = number field
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.value = parseFloat(originalValue.replace(/[^\d.\d]/g, '')) // Remove currency symbols
        } else {
            // title, date, and category = text input field (Category to dropdown)
            inputElement = document.createElement('input');
            inputElement.type = "text";
            inputElement.value = originalValue;
        }

        // Replace target element with input field
        event.target.innerHTML = '';
        event.target.appendChild(inputElement);

        // Focus on the input field (Place cursor inside/Make editable not eatable)
        inputElement.focus();

        // When user presses Enter, save changes
        inputElement.addEventListener('blur', function() {
            var newValue = inputElement.value.trim();

            // If the value has changed, update the DOM & send changes to flask server
            if (newValue !== originalValue) {

                if (field === 'amount') {
                    const format = { style: 'currency', currency: 'USD' };
                    const numberFormat = new Intl.NumberFormat('en-US', format);
                    newValue = numberFormat.format(newValue);
                    newValue = "-" + newValue
                }

                // Replace input feild w/new value
                event.target.textContent = newValue;

                // Send changes to update the server (AJAX? - Dynamic updates)
                console.log("Sending changes to database!");
                saveTransactionField(transactionId, field, newValue);
            } else {
                // If no changes, revert to original text
                event.target.textContent = originalValue;
            }
        });

        // When Enter is pressed, simulate blur effect (save)
        inputElement.addEventListener('keydown', function(e) {
            if (e.key === "Enter") {
                inputElement.blur();
            }
        });
    }

    // Function to send updated data to server (AJAX request)
    function saveTransactionField(transactionId, field, newValue) {
        // Arrow Function : => (Used for defining functions)

        const data = {
            id: transactionId,
            field: field,
            value: newValue
        };

        fetch('/update_transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Transaction updated:", data);
        })
        .catch((error) => {
            console.error("Error:", error);
        });
    }

});
