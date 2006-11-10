<?php

//TODO: serve ancora? Anche se faccio il logging ogni volta con index.php per evitare i timeout?
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
