function load_input_cychall(submissionid, key, input) {
    var field = $("form#task input[name='" + key + "']");
    if(key in input)
        $(field).prop('value', input[key]);
    else
        $(field).prop('value', "");
}

function studio_init_template_cychall(well, pid, problem)
{ 
    if("exercice" in problem) {
        var exercice_selector = $('#exercice-' + pid, well);
        exercice_selector.val(problem["exercice"]).change();

        studio_update_difficulty();
        exercice_selector.change(studio_update_difficulty);
    }

    if("difficulty" in problem)
        $('#difficulty-' + pid, well).val(problem["difficulty"]).change();

    if("modify" in problem)
        $('#modify-' + pid, well).attr("checked", problem["modify"]);
}

function studio_update_difficulty() {
    var exercice_id = $('select[id^=exercice] :selected').attr('class');
    var difficulty_selector = $('select[id^=difficulty]');
    $('option', difficulty_selector).hide();
    difficulty_selector.val([]);
    $('option.' + exercice_id, difficulty_selector).show();
}

function load_feedback_cychall(key, content) {
    load_feedback_code(key, content);
}


function reload_options(problem_id){
    var difficulty = $("#difficulty-selector" + '-' + problem_id).val();
    var exercise = $("#exercise-selector" + '-' + problem_id).val();
    studio_update_exercise_options({"problem_id": problem_id, "difficulty": difficulty, "exercise": exercise}, "GET");
}


 function studio_update_exercise_options(data, method)
{
    if(data == undefined)
        data = {};
    if(method == undefined)
        method = "GET";
    var problem_id = data["problem_id"];
    jQuery.ajax({
        success:    function(data)
                    {
                        console.log(problem_id);
                        console.log($("#exercise-options" + '-' + problem_id));
                        $("#exercise-options" + '-' + problem_id).replaceWith(data);
                    },
        method:     method,
        data:       data,
        url:        location.pathname + "/exercise_options"
    });
}