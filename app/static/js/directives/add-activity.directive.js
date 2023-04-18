/* jshint unused:vars */
'use strict';

angular.module('add.activity.directive', [])

.directive('addActivity', ['$uibModal', 'USER_ROLES', function($uibModal, USER_ROLES) {
	return {
		transclude: true,
		restrict: 'EA',
		template: '<div class="div-btn-add form-group">'+
					'<button type="button" class="btn btn-primary btn-fab add-activity" ng-click="show()">'+
						'<i class="material-icons">add</i>'+
					'</button>'+
				  '</div>',
		scope: {
			useTemplateUrl: '@',
			useCtrl: '@',
			useCtrlAlias: '@',
			formSize: '@',
			windowClass: '@',
			config:'=',
			updateAfterAdd: '&'
		},
		link: function(scope, element, attrs) {
			scope.show = function(){
				var modalScope = scope.$new();
				var modalInstance = $uibModal.open({
					animation: true,
					backdrop  : 'static',
					templateUrl: scope.useTemplateUrl,
					controller:  scope.useCtrl,
					controllerAs: scope.useCtrlAlias,
					size: scope.formSize,
					windowClass: scope.windowClass,
					scope: modalScope,
					resolve:{
						config: function() {
							return scope.config;
						},
						user: ['AuthService', function(AuthService) {
							return AuthService.GetUser();
						}]
					}
				});
				modalInstance.result.then(function (result) {
					scope.updateAfterAdd({data: result});
				}, function (error) {
					console.log('Modal dismissed at: ' + new Date());
				});
			};
		}
	};
}]);
