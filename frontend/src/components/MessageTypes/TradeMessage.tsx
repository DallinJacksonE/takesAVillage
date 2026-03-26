import React from "react";
import { MessageDTO } from "../../../../dtos";

const getFirstItem = (items: Record<string, number> | undefined) => {
	if (!items) {
		return { type: "food", amount: 0 };
	}
	const keys = Object.keys(items);
	if (keys.length === 0) {
		return { type: "food", amount: 0 };
	}
	const type = keys[0];
	return { type, amount: items[type] };
};

interface Props {
	msg: MessageDTO;
	isEditing: boolean;
	barterValues: Partial<MessageDTO>;
	setBarterValues: (values: Partial<MessageDTO>) => void;
}

const TradeMessage: React.FC<Props> = ({
	msg,
	isEditing,
	barterValues,
	setBarterValues,
}) => {
	const inputStyle = { width: "70px", padding: "4px", marginRight: "4px" };
	const selectStyle = { padding: "4px", marginRight: "4px" };

	if (isEditing) {
		const offer = getFirstItem(barterValues.offer_items || {});
		const request = getFirstItem(barterValues.request_items || {});

		return (
			<div
				style={{
					display: "flex",
					gap: "5px",
					alignItems: "center",
					flexWrap: "wrap",
				}}
			>
				<span>Give</span>
				<input
					type='number'
					style={inputStyle}
					value={offer.amount}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							offer_items: { [offer.type]: Number(e.target.value) },
						})
					}
				/>
				<select
					style={selectStyle}
					value={offer.type}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							offer_items: { [e.target.value]: offer.amount },
						})
					}
				>
					<option value='food'>Food</option>
					<option value='wood'>Wood</option>
					<option value='iron'>Iron</option>
				</select>
				<span>for</span>
				<input
					type='number'
					style={inputStyle}
					value={request.amount}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							request_items: { [request.type]: Number(e.target.value) },
						})
					}
				/>
				<select
					style={selectStyle}
					value={request.type}
					onChange={(e) =>
						setBarterValues({
							...barterValues,
							request_items: { [e.target.value]: request.amount },
						})
					}
				>
					<option value='food'>Food</option>
					<option value='wood'>Wood</option>
					<option value='iron'>Iron</option>
				</select>
			</div>
		);
	}

	const o = getFirstItem(msg.offer_items);
	const r = getFirstItem(msg.request_items);
	const displayOffer = `${o.amount} ${o.type}`;
	const displayRequest = `${r.amount} ${r.type}`;

	return (
		<span>
			<strong>Trade:</strong> {displayOffer} ↔ {displayRequest}
			{msg.bartered && (
				<span style={{ fontStyle: "italic", color: "#888", marginLeft: "5px" }}>
					(Counter Offer)
				</span>
			)}
		</span>
	);
};

export default TradeMessage;
