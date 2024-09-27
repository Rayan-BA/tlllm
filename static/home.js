var eventSource = new EventSource("/subscribe")

const appendMessage = (sender, message) => {
    var model = null
    if (sender !== "human") {
        model = message.split(":")[0]
        message = message.split(":")[1]
    }

    const card = document.createElement("div")
    card.setAttribute("class", sender + " card")
    const card_body = document.createElement("div")
    card_body.setAttribute("class", "card-body")
    card_body.innerText = message
    card.appendChild(card_body)

    const cont = document.createElement("div")

    // var justify = "justify-content-end"
    if (sender !== "human") {
        // justify = "justify-content-start"
        const details = document.createElement("span")
        details.setAttribute("class", "msg-details text-secondary")
        details.innerText = model
        cont.appendChild(details)
    }

    // cont.setAttribute("class", "d-flex flex-column")
    cont.appendChild(card)
    document.getElementById("text-box").appendChild(cont)
}

eventSource.onmessage = (event) => {
    var data = event.data

    appendMessage("bot", data)

    const outputContainer = document.getElementById("text-cont")
    outputContainer.scrollTop = outputContainer.scrollHeight
}

const post = (url, message) => {
    if (message.trim().length === 0) return // whitespace only

    const xhr = new XMLHttpRequest()
    xhr.open('POST', url, true)
    xhr.setRequestHeader('Content-type', 'text/plain; charset=UTF-8')
    xhr.send(message)

    appendMessage("human", message)
}

const publish = () => {
    var message = document.getElementById("prompt")
    post('/publish', message.value.trim())
    message.value = ""
}

document.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        if (!event.shiftKey) {
            publish()
        } else {
            this.value = val + "\n"
        }
        event.preventDefault()
    }
})