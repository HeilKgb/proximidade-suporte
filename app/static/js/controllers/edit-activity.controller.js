/* jshint unused:vars */
'use strict';

angular.module('edit-activity.controller', [])

.controller('EditActivityCtrl', ['$scope', '$uibModalInstance', 'DataService', 'Notify', 'activity', 'config', 'organizations',
  function($scope, $uibModalInstance, DataService, Notify, activity, config, organizations){

	var ctrl = this;
	$scope.title = 'Editar';

	$scope.config = angular.copy(config);
	$scope.activity = angular.copy(activity);
	$scope.organizations = angular.copy(organizations);
	$scope.dataloading = false;

	$scope.Cancel = function(){
		$uibModalInstance.dismiss("close");
	};

	$scope.OnSelect = function($item, $select) {
	};

	$scope.OnRemove = function($item, $select) {
	};

	$scope.SetPristine = function(form){
		if(form)
			form.$setPristine();
	};

	$scope.Reset = function(form){
		if(form)
			form.reset();
	};

	$scope.dataloading = false;
	$scope.Submit = function (form){
		if(form.$valid){
			if(form.modified){
				var data = $scope.ModifiedFields(form);
				$scope.dataloading = true;
				var trello_data = {}
				if (_.has($scope.activity, 'trello_cardId')){
					trello_data['id'] = $scope.activity.trello_cardId;
					if (_.has(data, 'title'))
						trello_data['name'] = data.title;
					if (_.has(data, 'description'))
						trello_data['desc'] = data.description;
					if (_.has(data, 'organizations'))
						organizations = data.organizations;
				}
				DataService.UpdateActivity({
					data: data,
					trello_data: trello_data,
					method: 'PUT',
					url: '/activities/' + $scope.activity.id,
				}).then(function(response){
					$scope.dataloading = false;
					var activity = response.activity;
					Notify.success({
						title: 'Atualização',
						message: 'A solicitação <span class="notify-texto">"' + activity.title + '"</span> foi atualizada com sucesso.',
						position: 'right',
						duration: 5000,
						container: angular.element(document.querySelector("#id_notify"))
					});
					$uibModalInstance.close(activity);
				}, function(error){
					$scope.dataloading = false;
					Notify.error({
						message: "Não foi possível atualizar a solicitação.\n (" + error.data.message + ")",
						title: "Erro",
						position: 'right',
						duration: 5000,
						container: angular.element(document.querySelector("#id_notify"))
					});
					console.log(error);
				});
			}
		}
	};
	$uibModalInstance.rendered.then(function(){
		if($scope.activity && ctrl && ctrl.form)
			$scope.SetPristine(ctrl.form);
	});

	$scope.ModifiedFields = function(form){
		var findField = function(childform, parent){
			var fields = {};
			if(childform.$name != 'nestedForm'){
				var name = childform.$name;
				if(parent[name].modifiedCount){
					var model = parent[name].modifiedModels[0];
					var key = model.$name;
					var value = model.$modelValue;
					fields[key]=value;
				}
			}
			else{

				if(childform.modifiedChildFormsCount){
					_.forEach(childform.modifiedChildForms, function(child){
						var f = findField(child, childform);
						Object.assign(fields,f);
					});
				}
			}
			return fields;
		};

		var fields = {};
		if(form.modified){
			if(form.modifiedChildFormsCount){
				_.forEach(form.modifiedChildForms, function(childform){
					var field = findField(childform, form);
					Object.assign(fields,field);
				})
			}
			if(form.modifiedCount){
				_.forEach(form.modifiedModels, function(model){
					var key = model.$name;
					var value = model.$modelValue;
					if(key != '')
					fields[key] = value;
				})
			}
		}
		return fields;
	};
}])
