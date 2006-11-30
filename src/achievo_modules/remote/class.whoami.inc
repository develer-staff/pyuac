<?php
include_once (moduleDir("remote")."class.timereg.inc");

class whoami extends atkNode
{
    function whoami()
    {
        $this->atkNode("whoami");
        $this->setSecurityAlias("remote.timereg");      
    }

    function action_search()
    {
        atkdebug("Action search");
        $user = getUser();
        echo make_xml("whoami", "OK", array(array('id'=>$user['id'], 'name'=>$user['name'])));
        exit;
    }
}
?>
