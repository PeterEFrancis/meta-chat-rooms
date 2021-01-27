function format_chatstream(chatstream, self) {

  let chat_box = document.createElement('div'); chat_box.classList.add('chat-box');


  // split on sender IDs
  let groups = [];
  let group;

  let last = "";
  for (let chat of chatstream) {
    if (last != chat.sender_id) {
      last = chat.sender_id;
      group = {
        'sender_name':chat.sender_name,
        'chats':[]
      };
      groups.push(group);
    }
    group.chats.push(chat);
  }

  for (let group of groups) {
    let bubble_group = document.createElement('div'); bubble_group.classList.add('bubble-group');
    let name = document.createElement('p'); name.classList.add('name');
    name.innerHTML = group.sender_name;
    bubble_group.appendChild(name);

    for (let chat of group.chats) {
      let bubble_container = document.createElement('div'); bubble_container.classList.add('bubble-container');
      let bubble = document.createElement('div'); bubble.classList.add('bubble');
      bubble.appendChild(document.createTextNode(chat.message));

      if (chat.sender_id == self) {
        bubble.classList.add('bubble-right');
        name.classList.add('name-right');
      } else {
        bubble.classList.add('bubble-left');
        name.classList.add('name-left');
      }

      bubble_container.appendChild(bubble);
      bubble_group.appendChild(bubble_container);
    }

    chat_box.appendChild(bubble_group);
  }

  return chat_box;
}
