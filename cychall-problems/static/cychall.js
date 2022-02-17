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