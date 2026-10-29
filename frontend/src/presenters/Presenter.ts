import { View } from "./View";

export abstract class Presenter<T extends View> {
	protected _view: T;

	constructor(view: T) {
		this._view = view;
	}
}
