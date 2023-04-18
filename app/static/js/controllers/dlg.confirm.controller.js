'use strict';

angular.module('dlg.confirm.controller',['dlg.confirm.service', 'dlg.confirm.directive'])

.controller('DlgConfirmCtrl', ["$scope", "$uibModalInstance", "dlgData", function ($scope, $uibModalInstance, dlgData) {
	$scope.data = angular.copy(dlgData);

	$scope.ok = function (closeMessage) {
		$uibModalInstance.close(closeMessage);
	};

	$scope.cancel = function (dismissMessage) {
		if (angular.isUndefined(dismissMessage)) {
			dismissMessage = 'cancel';
		}
		$uibModalInstance.dismiss(dismissMessage);
	};
}]);

