import React from "react";
import { TextMessageDTO } from "../../../../dtos";

interface Props {
  msg: TextMessageDTO;
}

const ChatMessage: React.FC<Props> = ({ msg }) => {
  return <span>{msg.content}</span>;
};

export default ChatMessage;
