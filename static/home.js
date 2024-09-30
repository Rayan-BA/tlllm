var socket = io()
socket.emit("client connect", { "msg": "client" })

const appendMessage = (sender, message) => {
    var model = null
    model = message.split(":")[0]
    message = message.split(":")[1]
    const card = document.createElement("div")
    card.setAttribute("class", sender + " card")
    const card_body = document.createElement("div")
    card_body.setAttribute("class", "card-body")
    card_body.innerText = message
    card.appendChild(card_body)
    const cont = document.createElement("div")
    const details = document.createElement("span")
    details.setAttribute("class", "msg-details text-secondary")
    details.innerText = model
    cont.appendChild(details)
    cont.appendChild(card)
    document.getElementById("text-box").appendChild(cont)
}

const post = () => {
    const urlParams = new URLSearchParams(document.location.search)
    const chat_id = urlParams.get("chat")
    var message = document.getElementById("prompt")
    socket.emit("user message", { "content": message.value, "chat_id": chat_id })
    appendMessage("human", "You:" + message.value)
    message.value = ""
}

socket.on("llm message", (message) => {
    appendMessage("bot", message)
})

// Send on enter, new line on shift + enter
document.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        if (!event.shiftKey) {
            post()
        } else {
            this.value = val + "\n"
        }
        event.preventDefault()
    }
})