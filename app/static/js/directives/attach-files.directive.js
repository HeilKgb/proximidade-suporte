/* jshint unused:vars */
'use strict';

angular.module('attach-files.directive', [])

.directive('attachFiles', ['$uibModal', function($uibModal) {
	return {
		transclude: true,
		replace: true,
		restrict: 'EA',
		template: '<div class="form-group is-empty is-fileinput append-file">'+
			'<input id="append-file" type="file" name="file" title="Clique aqui para adicionar arquivos"  multiple>'+
			'<button class="btn btn-sm btn-default">'+
			'<i class="material-icons">attach_file</i> Anexar'+
			'</button>'+
			'</div>',
		scope: {
			useTemplateUrl: '@',
			useCtrl: '@',
			usectrlAlias: '@',
			formSize: '@',
			windowClass: '@',
			attachments: '=',
			attachedFiles: '&',
			modalStatus: '=',
			actionType: '@'
		},
		link: function(scope, element, attrs) {
			element.bind('change', function(a, b) {

				if(scope.modalStatus.isOpen) return;
				scope.modalStatus.isOpen = true;

				console.log('update');
				var input = document.getElementById('append-file');
				var files = input.files;

				var modalScope = scope.$new();
				modalScope.files = files;
				modalScope.actionType = scope.actionType;
				var modalInstance = $uibModal.open({
					animation: true,
					backdrop  : 'static',
					templateUrl: scope.useTemplateUrl,
					controller:  scope.useCtrl,
					controllerAs: scope.useCtrlAs,
					size: scope.formSize,
					windowClass: scope.windowClass,
					scope: modalScope,
					resolve:{
						attachments: function() {
							return scope.attachments;
						}
					}
				});

				modalInstance.result.then(function (response) {
					scope.modalStatus.isOpen = false;
					scope.attachedFiles({attachments: response.attachments});
				}, function (error) {
					scope.modalStatus.isOpen = false;
					var input = document.getElementById('append-file');
					input.value = "";
					console.log('Modal dismissed at: ' + new Date());
				});
			});
		}
	};
}]);
