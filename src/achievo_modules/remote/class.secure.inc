<?php

class secure extends atkNode
{
	function secure()
	{
		$this->atkNode("secure");
	}

	function action_search()
	{
		$user = getUser();
		echo $user["id"];
		exit;
	}
}
?>
