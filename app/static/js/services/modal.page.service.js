'use strict';

angular.module('modal.page.service', ['ui.bootstrap.modal'])

.factory('$ModalPage', ["$uibModal", function ($uibModal) {
	return function (dlgData, dlgsettings) {

		if ('templateUrl' in dlgsettings && 'template' in dlgsettings) {
			delete dlgsettings.template;
		}

		if (dlgsettings.resolve == undefined)
			dlgsettings.resolve = {};

		_.forEach(dlgData, function(val, name){
			dlgsettings.resolve[name] = val;
		});

		return $uibModal.open(dlgsettings).result;

	};
}]);
