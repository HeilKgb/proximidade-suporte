/* jshint unused:vars */
'use strict';

angular.module('dlg.confirm.service', ['ui.bootstrap.modal'])

.value('$dlgConfirmDefaults', {
	template: '<div class="dlg-confirm">'+
					'<div class="modal-header" ng-bind-html="data.header"></div>'+
					'<div class="modal-body">'+
						'<div class="lead" ng-bind-html="data.text"></div>'+
						'<abm-form-group ng-if="data.again!=undefined">'+
							'<div class="checkbox confirm-again" abm-checkbox label="{{data.again}}">'+
								'<input name="confirm" type="checkbox" ng-model="data.status">'+
							'</div>'+
						'</abm-form-group>'+
					'</div>'+
					'<div class="modal-footer">'+
						'<button class="btn btn-default" ng-click="cancel(data)">{{data.cancel}}</button>'+
						'<button class="btn btn-primary" ng-click="ok(data)">{{data.ok}}</button>'+
					'</div>'+
				'</div>',
	controller: 'DlgConfirmCtrl',
	Labels: {
		title: 'Confirm',
		ok: 'OK',
		cancel: 'Cancel'
	}
})

.factory('$dlgConfirm', ["$uibModal", "$dlgConfirmDefaults", function ($uibModal, $dlgConfirmDefaults) {
	return function (dlgData, dlgsettings) {
		var defaults = angular.copy($dlgConfirmDefaults);
		dlgsettings = angular.extend(defaults, (dlgsettings || {}));

		dlgData = angular.extend({}, dlgsettings.Labels, dlgData || {});

		if ('templateUrl' in dlgsettings && 'template' in dlgsettings) {
			delete dlgsettings.template;
		}

		dlgsettings.resolve = {
			dlgData: function () {
				return dlgData;
			}
		};

		return $uibModal.open(dlgsettings).result;
	};
}])
//==============================================================================================================================
.value('$dlgConfirmDelDefaults', {
	template: '<div class="dlg-confirm-del">'+
					'<div class="modal-header" ng-bind-html="data.header"></div>'+
						'<div class="modal-body">'+
							'<p class="lead" ng-bind-html="data.text"></p>'+
							'<div class="modal-form-group alertas-actions text-right">'+
							'<button type="button" class="btn btn-default" ng-click="Cancel(data)">{{data.Cancel}}</button>'+
							'<button type="button" class="btn btn-primary" ng-click="Ok(data)">{{data.Ok}}</button>'+
						'</div>'+
					'</div>'+
				'</div>',
	controller: 'DlgConfirmDelCtrl',
	Labels: {
		title: 'Confirm',
		ok: 'OK',
		cancel: 'Cancel'
	}
})

.factory('$dlgConfirmDel', ["$uibModal", "$dlgConfirmDelDefaults", function ($uibModal, $dlgConfirmDelDefaults) {
	return function (dlgData, dlgsettings) {
		var defaults = angular.copy($dlgConfirmDelDefaults);
		dlgsettings = angular.extend(defaults, (dlgsettings || {}));

		dlgData = angular.extend({}, dlgsettings.Labels, dlgData || {});

		if ('templateUrl' in dlgsettings && 'template' in dlgsettings) {
			delete dlgsettings.template;
		}

		dlgsettings.resolve = {
			dlgData: function () {
				return dlgData;
			}
		};

		return $uibModal.open(dlgsettings).result;
	};
}]);
