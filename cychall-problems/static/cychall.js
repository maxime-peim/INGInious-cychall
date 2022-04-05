function load_input_cychall(submissionid, key, input) {
    var field = $("form#task input[name='" + key + "']");
    if(key in input)
        $(field).prop('value', input[key]);
    else
        $(field).prop('value', "");
}

function studio_init_template_cychall(well, pid, problem)
{
    if("exercise-path" in problem) {
        var exercise_selector = $('#exercise-selector-' + pid, well);
        exercise_selector.val(problem["exercise-path"]).change();

        studio_update_difficulty();
        exercise_selector.change(studio_update_difficulty);
    }

    if("difficulty" in problem)
        $('#difficulty-selector-' + pid, well).val(problem["difficulty"]).change();

    reload_options(pid);
}

function studio_update_difficulty() {
    var exercise_id = $('select[id^=exercise-selector] :selected').attr('class');
    var difficulty_selector = $('select[id^=difficulty-selector]');
    $('option', difficulty_selector).hide();
    difficulty_selector.val([]);
    $('option.' + exercise_id, difficulty_selector).show();
}

function load_feedback_cychall(key, content) {
    load_feedback_code(key, content);
}

/**
 * Display a message indicating the status of a save action
 */
 function studio_display_template_submit_message(title, content, type, dismissible)
 {
     var code = getAlertCode(title, content, type, dismissible);
     $('#template_edit_submit_status').html(code);
 
     if(dismissible)
     {
         window.setTimeout(function()
         {
             $("#template_edit_submit_status").children().fadeTo(1000, 0).slideUp(1000, function()
             {
                 $(this).remove();
             });
         }, 3000);
     }
 }

 /**
 * Submit the form
 */
var studio_template_submitting = false;
function studio_template_submit()
{
    if(studio_template_submitting)
        return;
    studio_template_submitting = true;

    studio_display_template_submit_message("Saving...", "", "info", false);

    var error = "";
    $('.template_edit_submit_button').attr('disabled', true);

    $.each(codeEditors, function(path, editor) {
        if(path in studio_file_editor_tabs) {
            jQuery.ajax({
                success: function (data) {
                    if ("error" in data)
                        error += "<li>An error occurred while saving the file " + path + "</li>";
                    else
                        editor.markClean();
                },
                url: location.pathname + "/files",
                method: "POST",
                dataType: "json",
                data: {"path": path, "action": "edit_save", "content": editor.getValue()},
                async: false
            });
        }
    });

    if(error)
        studio_display_template_submit_message("Some error(s) occurred when saving the template: <ul>" + error + "</ul>", "", "danger", true);
    else
        studio_display_template_submit_message("Template saved.", "", "success", true);

    $('.template_edit_submit_button').attr('disabled', false);
    studio_template_submitting = false;
}

function check_template_id(event)
{
    var template_id = $("#template_id").val();
    if(!template_id.match(/^[a-zA-Z0-9_\-]+$/)){
        alert('Template id should only contain alphanumeric characters (in addition to "_" and "-").');
        event.preventDefault();
        return false;
    }
    return true;
}

function open_delete_modal(button) {
	var name = button.closest('.template').id
    if($(button).hasClass("delete_template")){
        $('#delete_template_modal .templateid').val(name.slice(7));
    }
}

function reload_options(problem_id){
    var difficulty = $("#difficulty-selector-" + problem_id).val();
    var exercise_path = $("#exercise-selector-" + problem_id).val();
    studio_update_exercise_options({"problem_id": problem_id, "difficulty": difficulty, "exercise-path": exercise_path});
}


function studio_update_exercise_options(data, method)
{
    if(data == undefined)
        return;
    
    var problem_id = data["problem_id"];
    $.ajax({
        success:    function(data)
                    {
                        console.log(problem_id);
                        console.log($("#exercise-options-" + problem_id));
                        $("#exercise-options-" + problem_id).html(data);
                    },
        method:     method == undefined ? "POST" : method,
        data:       data,
        url:        location.pathname + "/exercise_options"
    });
}