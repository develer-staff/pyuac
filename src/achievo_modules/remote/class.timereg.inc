<?php
include_once (moduleDir("timestats")."class.hours.inc");

//XML stuff da http://www.xml.com/pub/a/2003/03/19/dive-into-xml.html
if (stristr($_SERVER[HTTP_ACCEPT], "application/xhtml+xml"))
    header("Content-Type: application/xhtml+xml");
else
    header("Content-Type: text/html");

function is_valid_date($date)
{
    $res = (ereg("([0-9]{4})[^0-9]{0,1}([0-9]{1,2})[^0-9]{0,1}([0-9]{1,2})", $date));
    //if ($res == 1) echo "Pass";
    //else echo "Fail";
    return $res;
}

function xml_encode($var)
{
    return htmlspecialchars($var, ENT_COMPAT, "iso-8859-1");
    //return str_replace(array("&gt;", "&lt;", "&quot;", "&amp;"), array(">", "<", "\"", "&"), $var);
}

function make_xml($node, $msg, $results, $bodykey="")
{
    $res  = '<?xml version="1.0" encoding="iso-8859-1"?>'."\n";
    $res .= '<response node="'.xml_encode($node).'" msg="'.xml_encode($msg).'" len="'.count($results).'">'."\n";
    foreach ($results as $r)
    {
        $res .= "<record";
        foreach ($r as $key=>$value)
        {
            if ($key != $bodykey)
                $res .= ' '.xml_encode($key).'="'.xml_encode($value).'"';
        }
        if (array_key_exists($bodykey, $r))
        {
            $res .= ">";
            $res .= xml_encode($r[$bodykey]);
            $res .= "</record>\n";
        }
        else
            $res .= " />\n";

    }
    $res .= '</response>';
    return $res;
}

class timereg extends atkNode
{
    function timereg()
    {
        $this->atkNode("timereg");
    }

    function action_save()
    {
        atkdebug("timereg Action save");
        $hoursnode = &atkGetNode("timereg.hours");
        $hoursnode->m_postvars = $this->m_postvars; // Share postvars.
        $record = $hoursnode->updateRecord();

        $hoursnode->preAdd($record);
        $hoursnode->validate($record, "add");

        $error = count($record['atkerror']) > 0;
        foreach (array_keys($record) as $key)
            $error = $error || (is_array($record[$key]) && count($record[$key]['atkerror']) > 0);

        if ($error)
        {
            echo make_xml("timereg", "Err", array(array("Err"=>print_r($record, True))));
        }
        else
        {
            $hoursnode->addDb($record, true, "add");
            echo make_xml("timereg", "OK", array(array("action"=>"save")));
        }
        exit;
    }

    function action_edit()
    {
        atkdebug("timereg Action edit");
        $hoursnode = &atkGetNode("timereg.hours");
        $hoursnode->m_postvars = $this->m_postvars; // Share postvars.
        $record = $hoursnode->updateRecord();

        $hoursnode->preUpdate($record);
        $hoursnode->validate($record, "update");

        $error = count($record['atkerror']) > 0;
        foreach (array_keys($record) as $key)
            $error = $error || (is_array($record[$key]) && count($record[$key]['atkerror']) > 0);

        if ($error)
        {
            echo make_xml("timereg", "Err", array(array("Err"=>print_r($record, True))));
        }
        else
        {
            $hoursnode->updateDb($record);
            echo make_xml("timereg", "OK", array(array("action"=>"edit")));
        }
        exit;
    }

    function action_delete()
    {
        atkdebug("timereg Action delete");
        $hoursnode = &atkGetNode("timereg.hours");
        $hoursnode->m_postvars = $this->m_postvars; // Share postvars.
        //TODO: callHandler semplifica la delegazione, ma la gestione degli errori?
        $hoursnode->callHandler("delete");
        echo make_xml("timereg", "OK", array(array("action"=>"delete")));
        exit;
    }
}
?>
