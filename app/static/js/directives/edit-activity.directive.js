/* jshint unused:vars */
'use strict';

angular.module('edit-activity.directive', [])

.directive('editActivity', ['$uibModal', 'USER_ROLES', function($uibModal, USER_ROLES) {
	return {
		transclude: true,
		replace: true,
		restrict: 'EA',
		template:  '<a href="#" ng-click="show()">Editar<i class="material-icons">edit</i></a>',
		scope: {
			useTemplateUrl: '@',
			useCtrl: '@',
			useCtrlAs: '@',
			formSize: '@',
			windowClass: '@',
			config: '=',
			activity: '=',
			updateAfterEdit: '&',
		},
		link: function(scope, element, attrs) {
			scope.show = function(){
				var modalScope = scope.$new();
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
						config: function(){
							return scope.config;
						},
						activity: function(){
							return scope.activity;
						},
						organizations: ['DataService', function(DataService) {
							return DataService.GetOrganizations({method: 'GET', url: '/organizations'});
						}]
					}
				});
				modalInstance.result.then(function (result) {
					scope.updateAfterEdit({data: result});
					console.log('Modal ok' + result);
				}, function (error) {
					console.log('Modal dismissed at: ' + new Date());
				});
			};
		}
	};
}]);
