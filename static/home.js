var socket = io()

const appendMessage = (message, username) => {
    // var model = null
    // model = message.split(":")[0]
    // message = message.split(":")[1]
    const card = document.createElement("div")
    card.setAttribute("class", "card")
    if (message.user.username === username) {
        card.setAttribute("style", "background-color: rgb(184, 234, 244);")
    }
    const card_body = document.createElement("div")
    card_body.setAttribute("class", "card-body")
    card_body.innerText = message.content
    card.appendChild(card_body)
    const cont = document.createElement("div")
    const details = document.createElement("span")
    details.setAttribute("class", "msg-details text-secondary")
    details.innerText = message.user.username
    cont.appendChild(details)
    cont.appendChild(card)
    document.getElementById("text-box").appendChild(cont)
}

const post = () => {
    const splitURL = document.URL.split("/")
    const chat_id = splitURL[splitURL.length - 1]
    var message = document.getElementById("prompt")
    var username = document.cookie.split("=")[1]
    socket.emit("user prompt", { "content": message.value, "chat_id": chat_id })
    try { document.getElementById("fresh_chat").remove() } catch { }
    appendMessage({ "content": message.value, "user": { "username": username } }, username)
    message.value = ""
}

const setActive = (el) => {
    el.className += " active"
}

// socket.on("user message", (message) => {
//     appendMessage(message)
// })

socket.on("llm message", (message) => {
    appendMessage(message)
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