/* jshint unused:vars */
'use strict';

angular.module('dlg.confirm.directive', [])

.directive('dlgConfirm', ["$dlgConfirm", "$timeout", function ($dlgConfirm, $timeout) {
	return {
		priority: 1,
		restrict: 'A',
		scope: {
			dlgConfirmIf: "=",
			ngClick: '&',
			dlgConfirmTxt: '@',
			dlgConfirmSettings: "=",
			dlgConfirmHeader:'@',
			dlgConfirmAgain:'@',
			dlgConfirmOk: '@',
			dlgConfirmCancel: '@',
			dlgConfirmStatus: "=",
			dlgConfirmClickOk: '&',
			dlgConfirmClickCancel: '&'
		},
		link: function (scope, element, attrs) {

			function onSuccess(response) {
				var rEl = element[0];
				if (["checkbox", "radio"].indexOf(rEl.type) != -1) {
					var model = element.data('$ngModelController');
					if (model) {
						model.$setViewValue(!rEl.checked);
						model.$render();
					} else {
						rEl.checked = !rEl.checked;
					}
				}
				if(scope.dlgConfirmClickOk)
					scope.dlgConfirmClickOk({'response': response});
				scope.ngClick();
			}
			function onCancel(response) {
				if(scope.dlgConfirmClickCancel && typeof(response) === "object" && response.constructor === {}.constructor)
					scope.dlgConfirmClickCancel({'response': response});
			}

			element.unbind("click").bind("click", function ($event) {

				$event.preventDefault();

				$timeout(function() {

					if (angular.isUndefined(scope.dlgConfirmIf) || scope.dlgConfirmIf) {
						var data = {text: scope.dlgConfirmTxt};
						if (scope.dlgConfirmHeader) {
							data.header = scope.dlgConfirmHeader;
						}
						if (scope.dlgConfirmOk) {
							data.ok = scope.dlgConfirmOk;
						}
						if (scope.dlgConfirmCancel) {
							data.cancel = scope.dlgConfirmCancel;
						}
						if (scope.dlgConfirmAgain) {
							data.again = scope.dlgConfirmAgain;
						}
						if (scope.dlgConfirmStatus) {
							data.status = scope.dlgConfirmStatus;
						}
						$dlgConfirm(data, scope.dlgConfirmSettings || {}).then(onSuccess, onCancel);
					} else {
						scope.$apply(onSuccess);
					}

				});

			});

		}
	};
}]);
